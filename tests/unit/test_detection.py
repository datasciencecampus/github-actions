import pytest

from precommit_updates.detection import detect_updates
from precommit_updates.github import GitHubQueryError


def test_detection_includes_candidate_publication_timestamp(tmp_path):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hook"
    config.write_text("repos:\n" f"  - repo: {repo}\n" f"    rev: {'a' * 40}\n")
    tracking.write_text('{"hooks": {"https://github.com/example/hook": {"current_version": "v1.0.0"}}}')

    class GitHub:
        def latest_release(self, repo_url):
            return ("v1.0.1", "b" * 40, "2026-09-10T12:00:00Z")

    updates = detect_updates(config, tracking, GitHub())

    assert updates == [
        {
            "repo": repo,
            "old_sha": "a" * 40,
            "new_sha": "b" * 40,
            "old_version": "v1.0.0",
            "new_version": "v1.0.1",
            "candidate_published_at": "2026-09-10T12:00:00Z",
            "semver_level": "patch",
            "commit_range": f"{'a' * 40}...{'b' * 40}",
        }
    ]


def test_detection_fails_when_release_check_is_indeterminate(tmp_path):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    config.write_text(
        "repos:\n"
        "  - repo: https://github.com/example/hook\n"
        f"    rev: {'a' * 40}\n"
    )
    tracking.write_text('{"hooks": {}}')

    class FailingGitHub:
        def latest_release(self, repo_url):
            raise GitHubQueryError("rate limit exceeded")

    with pytest.raises(GitHubQueryError, match="rate limit exceeded"):
        detect_updates(config, tracking, FailingGitHub())