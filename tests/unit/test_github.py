from types import SimpleNamespace
import subprocess

import pytest

from precommit_updates.github import GitHubClient, GitHubQueryError, parse_repository_url


def test_parse_repository_url_accepts_git_suffix_and_rejects_other_hosts():
    assert parse_repository_url("https://github.com/example/hook.git").path == "example/hook"
    assert parse_repository_url("https://gitlab.com/example/hook") is None


def test_commit_messages_use_compare_range():
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="abc\ndef\n", stderr="")

    commits = GitHubClient(runner=runner).commit_messages(
        "https://github.com/example/hook", "oldsha", "newsha"
    )

    assert commits == ["abc", "def"]
    assert calls[0][0] == [
        "gh",
        "api",
        "repos/example/hook/compare/oldsha...newsha",
        "-q",
        ".commits[].sha",
    ]


def test_latest_release_returns_tag_sha_and_publication_time():
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if "releases/latest" in command[2]:
            return SimpleNamespace(returncode=0, stdout="v1.2.3\n2026-09-10T12:00:00Z\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="abc123\n", stderr="")

    release = GitHubClient(runner=runner).latest_release("https://github.com/example/hook")

    assert release == ("v1.2.3", "abc123", "2026-09-10T12:00:00Z")
    assert calls[0] == [
        "gh",
        "api",
        "repos/example/hook/releases/latest",
        "-q",
        '.tag_name + "\n" + .published_at',
    ]


def test_release_not_found_is_treated_as_missing_data():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="gh: Not Found (HTTP 404)")

    assert GitHubClient(runner=runner).latest_release("https://github.com/example/hook") is None


def test_latest_release_missing_publication_time_raises_query_error():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout="v1.2.3\n", stderr="")

    with pytest.raises(GitHubQueryError, match="published_at"):
        GitHubClient(runner=runner).latest_release("https://github.com/example/hook")


def test_failed_github_command_raises_query_error():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="failure")

    with pytest.raises(GitHubQueryError, match="failure"):
        GitHubClient(runner=runner).latest_release("https://github.com/example/hook")


def test_timed_out_github_command_raises_query_error():
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=10)

    with pytest.raises(GitHubQueryError, match="timed out"):
        GitHubClient(runner=runner).latest_release("https://github.com/example/hook")


def test_missing_gh_raises_query_error():
    def runner(command, **kwargs):
        raise FileNotFoundError("gh")

    with pytest.raises(GitHubQueryError, match="failed to start"):
        GitHubClient(runner=runner).latest_release("https://github.com/example/hook")