"""GitHub CLI adapter used by the update pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from typing import Callable, Optional, Sequence

from .models import parse_version


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
_REPOSITORY_PATTERN = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")


class GitHubQueryError(RuntimeError):
    """Raised when a GitHub API query could not be completed reliably."""


@dataclass(frozen=True)
class GitHubRepository:
    """Parsed owner and repository name from a GitHub URL.

    Attributes:
        owner: GitHub account or organization name.
        name: GitHub repository name.
    """

    owner: str
    name: str

    @property
    def path(self) -> str:
        """Return the ``owner/name`` path used by the GitHub API."""
        return f"{self.owner}/{self.name}"


def parse_repository_url(repo_url: str) -> Optional[GitHubRepository]:
    """Parse a HTTPS GitHub repository URL.

    Args:
        repo_url: Repository URL, optionally ending in ``.git`` or ``/``.

    Returns:
        A parsed repository, or ``None`` for a non-GitHub or malformed URL.
    """
    match = _REPOSITORY_PATTERN.fullmatch(repo_url.strip())
    if not match:
        return None
    return GitHubRepository(*match.groups())


class GitHubClient:
    """Run read-only GitHub API queries through the ``gh`` executable."""

    def __init__(self, runner: CommandRunner | None = None, timeout: int = 10) -> None:
        """Initialize a GitHub CLI client.

        Args:
            runner: Callable used to execute commands; defaults to ``subprocess.run``.
            timeout: Maximum seconds allowed for each GitHub API request.
        """
        self._runner = runner or subprocess.run
        self._timeout = timeout

    def _query(self, args: Sequence[str], *, missing_ok: bool = False) -> Optional[str]:
        """Run a read-only ``gh api`` query.

        Args:
            args: Arguments appended after ``gh api``.
            missing_ok: Whether a GitHub 404 should be treated as absent data.

        Returns:
            Stripped standard output, or ``None`` when the requested data is absent.

        Raises:
            GitHubQueryError: If the query fails, times out, or ``gh`` cannot be run.
        """
        command = ["gh", "api", *args]
        try:
            result = self._runner(
                command,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise GitHubQueryError(f"GitHub API query timed out: {' '.join(command)}") from error
        except OSError as error:
            raise GitHubQueryError(f"GitHub API query failed to start: {error}") from error
        if result.returncode != 0:
            if missing_ok and _is_not_found(result):
                return None
            detail = (result.stderr or result.stdout or "unknown error").strip()
            raise GitHubQueryError(f"GitHub API query failed: {detail}")
        if not result.stdout.strip():
            return None
        return result.stdout.strip()

    def latest_tag(self, repo_url: str) -> Optional[tuple[str, str]]:
        """Return the highest semantic version tag and its resolved commit SHA.

        Args:
            repo_url: Upstream GitHub repository URL.

        Returns:
            A ``(tag, sha)`` tuple, or ``None`` when the repository has no semantic version tags.
        """
        repository = parse_repository_url(repo_url)
        if not repository:
            return None
        tags = self._query(
            ["--paginate", f"repos/{repository.path}/tags", "-q", '.[] | [.name, .commit.sha] | @tsv']
        )
        candidates: list[tuple[tuple[int, int, int], str, str]] = []
        for line in tags.splitlines() if tags else []:
            try:
                tag, sha = line.split("\t", 1)
            except ValueError:
                continue
            version = parse_version(tag)
            if version:
                candidates.append((version, tag, sha))
        if not candidates:
            return None
        _, tag, sha = max(candidates, key=lambda candidate: candidate[0])
        return tag, sha

    def latest_release(self, repo_url: str) -> Optional[tuple[str, str, str]]:
        """Return the latest release tag, resolved commit SHA, and publication time.

        Args:
            repo_url: Upstream GitHub repository URL.

        Returns:
            A ``(tag, sha, published_at)`` tuple, or ``None`` when the repository has no readable release.
        """
        repository = parse_repository_url(repo_url)
        if not repository:
            return None
        release = self._query(
            [f"repos/{repository.path}/releases/latest", "-q", '.tag_name + "\n" + .published_at'],
            missing_ok=True,
        )
        if not release:
            return None
        release_lines = release.splitlines()
        if len(release_lines) < 2:
            raise GitHubQueryError(f"Latest release for {repository.path} did not include published_at")
        tag = release_lines[0].strip()
        published_at = release_lines[1].strip()
        if not published_at:
            raise GitHubQueryError(f"Latest release for {repository.path} did not include published_at")
        sha = self._query([f"repos/{repository.path}/commits/{tag}", "-q", ".sha"])
        return (tag, sha, published_at) if sha else None

    def tag_for_sha(self, repo_url: str, sha: str) -> Optional[str]:
        """Find a tag pointing at a commit SHA.

        Args:
            repo_url: Upstream GitHub repository URL.
            sha: Commit SHA to resolve.

        Returns:
            The first matching tag, or ``None`` when no tag is found.
        """
        repository = parse_repository_url(repo_url)
        if not repository:
            return None
        query = f'.[] | select(.commit.sha == "{sha}") | .name'
        tags = self._query(["--paginate", f"repos/{repository.path}/tags", "-q", query])
        return tags.splitlines()[0] if tags else None

    def release_notes(self, repo_url: str, tag: str) -> Optional[str]:
        """Fetch release notes for a tag.

        Args:
            repo_url: Upstream GitHub repository URL.
            tag: Release tag to query.

        Returns:
            Release body text, or ``None`` when it cannot be fetched.
        """
        repository = parse_repository_url(repo_url)
        if not repository:
            return None
        return self._query([f"repos/{repository.path}/releases/tags/{tag}", "-q", ".body"], missing_ok=True)

    def commit_messages(self, repo_url: str, old_sha: str, new_sha: str) -> list[str]:
        """Fetch up to ten commits in an inclusive GitHub comparison range.

        Args:
            repo_url: Upstream GitHub repository URL.
            old_sha: Base commit for the comparison.
            new_sha: Head commit for the comparison.

        Returns:
            Commit SHAs from ``old_sha...new_sha``, truncated to ten entries.
        """
        repository = parse_repository_url(repo_url)
        if not repository:
            return []
        comparison = f"repos/{repository.path}/compare/{old_sha}...{new_sha}"
        commits = self._query([comparison, "-q", ".commits[].sha"])
        return commits.splitlines()[:10] if commits else []


def _is_not_found(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a failed ``gh api`` result is an expected GitHub 404."""
    output = f"{result.stderr}\n{result.stdout}"
    return "HTTP 404" in output or '"status":"404"' in output or '"status": "404"' in output