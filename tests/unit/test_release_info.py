from precommit_updates.github import GitHubComparison, GitHubQueryError
from precommit_updates.models import is_sha_like_version


def test_sha_detection_does_not_depend_on_repository_names():
    assert is_sha_like_version("0123456789abcdef" * 2 + "01234567")


def test_enrich_updates_uses_total_commit_count_for_comparison():
    from precommit_updates.release_info import enrich_updates

    class GitHub:
        def release_notes(self, repo_url, tag):
            return "notes"

        def comparison(self, repo_url, old_sha, new_sha):
            return GitHubComparison(commits=["a" * 40, "b" * 40], total_commits=12)

    enriched = enrich_updates(
        [
            {
                "repo": "https://github.com/example/hook",
                "old_sha": "old",
                "new_sha": "new",
                "new_version": "v1.2.3",
            }
        ],
        GitHub(),
    )

    assert enriched[0]["commits"] == ["a" * 40, "b" * 40]
    assert enriched[0]["commit_count"] == 12


def test_enrich_updates_falls_back_when_comparison_fails(capsys):
    from precommit_updates.release_info import enrich_updates

    class GitHub:
        def release_notes(self, repo_url, tag):
            return "notes"

        def comparison(self, repo_url, old_sha, new_sha):
            raise GitHubQueryError("comparison unavailable")

    enriched = enrich_updates(
        [
            {
                "repo": "https://github.com/example/hook",
                "old_sha": "old",
                "new_sha": "new",
                "new_version": "v1.2.3",
            }
        ],
        GitHub(),
    )

    assert enriched[0]["commits"] == []
    assert enriched[0]["commit_count"] == 0
    assert "comparison unavailable" in capsys.readouterr().out