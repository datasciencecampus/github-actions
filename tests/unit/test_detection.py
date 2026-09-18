import json
from datetime import datetime, timezone

import pytest

from precommit_updates.detection import detect_updates
from precommit_updates.github import GitHubQueryError


NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


def test_detection_includes_candidate_first_seen_timestamp(tmp_path):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hook"
    config.write_text("repos:\n" f"  - repo: {repo}\n" f"    rev: {'a' * 40}\n")
    tracking.write_text('{"hooks": {"https://github.com/example/hook": {"current_version": "v1.0.0"}}}')

    class GitHub:
        def latest_tag(self, repo_url):
            return "v1.0.1", "b" * 40

    updates = detect_updates(config, tracking, GitHub(), now=NOW)

    assert updates == [
        {
            "repo": repo,
            "old_sha": "a" * 40,
            "new_sha": "b" * 40,
            "old_version": "v1.0.0",
            "new_version": "v1.0.1",
            "candidate_first_seen_at": "2026-09-17T00:00:00+00:00",
            "semver_level": "patch",
            "commit_range": f"{'a' * 40}...{'b' * 40}",
        }
    ]
    state = json.loads(tracking.read_text())
    assert state["hooks"][repo]["candidate_updates"]["v1.0.1"] == {
        "sha": "b" * 40,
        "first_seen_at": "2026-09-17T00:00:00+00:00",
    }


def test_detection_reuses_existing_candidate_first_seen_timestamp(tmp_path):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hook"
    first_seen_at = "2026-09-01T00:00:00+00:00"
    config.write_text("repos:\n" f"  - repo: {repo}\n" f"    rev: {'a' * 40}\n")
    tracking.write_text(
        json.dumps(
            {
                "hooks": {
                    repo: {
                        "current_version": "v1.0.0",
                        "candidate_updates": {"v1.0.1": {"sha": "b" * 40, "first_seen_at": first_seen_at}},
                    }
                }
            }
        )
    )

    class GitHub:
        def latest_tag(self, repo_url):
            return "v1.0.1", "b" * 40

    updates = detect_updates(config, tracking, GitHub(), now=NOW)

    assert updates[0]["candidate_first_seen_at"] == first_seen_at


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
        def latest_tag(self, repo_url):
            raise GitHubQueryError("rate limit exceeded")

    with pytest.raises(GitHubQueryError, match="rate limit exceeded"):
        detect_updates(config, tracking, FailingGitHub())