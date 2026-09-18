from datetime import datetime, timezone

from precommit_updates.pr_body import generate_pr_body


def test_pr_body_uses_total_commit_count_for_summary():
    body = generate_pr_body(
        [
            {
                "repo": "https://github.com/example/hook",
                "old_sha": "a" * 40,
                "new_sha": "b" * 40,
                "old_version": "v1.0.0",
                "new_version": "v1.1.0",
                "semver_level": "minor",
                "commits": ["c" * 40, "d" * 40],
                "commit_count": 12,
                "cooldown_applied": {"minor": 14},
            }
        ],
        [],
        {"major": 28, "minor": 14, "patch": 7},
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )

    assert "<details><summary>Commits (12)</summary>" in body
    assert "- ccccccc" in body
    assert "- ddddddd" in body


def test_pr_body_escapes_html_in_release_notes():
    body = generate_pr_body(
        [
            {
                "repo": "https://github.com/example/hook",
                "old_sha": "a" * 40,
                "new_sha": "b" * 40,
                "old_version": "v1.0.0",
                "new_version": "v1.1.0",
                "semver_level": "minor",
                "release_notes": "</details><div>untrusted</div>",
            }
        ],
        [],
        {"major": 28, "minor": 14, "patch": 7},
    )

    assert "&lt;/details&gt;&lt;div&gt;untrusted&lt;/div&gt;" in body
    assert "</details><div>untrusted</div>" not in body
