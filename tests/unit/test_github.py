from types import SimpleNamespace
import subprocess

import pytest

from precommit_updates.github import GitHubClient, GitHubQueryError, parse_repository_url


def test_parse_repository_url_accepts_git_suffix_and_rejects_other_hosts():
    assert parse_repository_url("https://github.com/example/hook.git").path == "example/hook"
    assert parse_repository_url("https://gitlab.com/example/hook") is None


def test_comparison_uses_compare_range_and_total_commit_count():
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout='{"total_commits":12,"commits":["abc","def"]}\n', stderr="")

    comparison = GitHubClient(runner=runner).comparison(
        "https://github.com/example/hook", "oldsha", "newsha"
    )

    assert comparison.commits == ["abc", "def"]
    assert comparison.total_commits == 12
    assert calls[0][0] == [
        "gh",
        "api",
        "repos/example/hook/compare/oldsha...newsha",
        "-q",
        '{total_commits: .total_commits, commits: [.commits[:10][].sha]}',
    ]


def test_commit_messages_returns_bounded_comparison_commits():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout='{"total_commits":12,"commits":["abc","def"]}\n', stderr="")

    assert GitHubClient(runner=runner).commit_messages("https://github.com/example/hook", "oldsha", "newsha") == [
        "abc",
        "def",
    ]


def test_latest_tag_returns_highest_semver_tag_and_sha():
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(
            returncode=0,
            stdout="v1.2.0\taaa\nnot-semver\tbbb\nv1.10.0\tccc\n",
            stderr="",
        )

    assert GitHubClient(runner=runner).latest_tag("https://github.com/example/hook") == ("v1.10.0", "ccc")
    assert calls[0] == [
        "gh",
        "api",
        "--paginate",
        "repos/example/hook/tags",
        "-q",
        '.[] | [.name, .commit.sha] | @tsv',
    ]


def test_latest_tag_returns_none_when_no_semver_tags_exist():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout="not-semver\tabc\n", stderr="")

    assert GitHubClient(runner=runner).latest_tag("https://github.com/example/hook") is None


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
        GitHubClient(runner=runner).latest_tag("https://github.com/example/hook")


def test_timed_out_github_command_raises_query_error():
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=10)

    with pytest.raises(GitHubQueryError, match="timed out"):
        GitHubClient(runner=runner).latest_tag("https://github.com/example/hook")


def test_missing_gh_raises_query_error():
    def runner(command, **kwargs):
        raise FileNotFoundError("gh")

    with pytest.raises(GitHubQueryError, match="failed to start"):
        GitHubClient(runner=runner).latest_tag("https://github.com/example/hook")