import pytest

from precommit_updates.detection import detect_updates
from precommit_updates.github import GitHubQueryError


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