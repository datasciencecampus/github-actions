import json
from datetime import datetime, timezone

from precommit_updates.mutation import apply_updates


def test_apply_updates_preserves_yaml_comments_and_updates_only_changed_level(tmp_path):
    config_path = tmp_path / ".pre-commit-config.yaml"
    tracking_path = tmp_path / "tracking.json"
    config_path.write_text(
        "repos:\n  - repo: https://github.com/example/hook\n    rev: oldsha  # frozen: v1.0.0\n    hooks: []\n"
    )
    tracking_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "https://github.com/example/hook": {
                        "semver_levels": {"major": "old", "minor": "old", "patch": "old"},
                        "candidate_updates": {"v1.0.1": {"sha": "newsha", "first_seen_at": "old"}},
                    }
                }
            }
        )
    )

    apply_updates(
        config_path,
        tracking_path,
        [{"repo": "https://github.com/example/hook", "new_sha": "newsha", "new_version": "v1.0.1", "semver_level": "patch"}],
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )

    assert "rev: newsha  # frozen: v1.0.1" in config_path.read_text()
    tracking = json.loads(tracking_path.read_text())
    assert tracking["hooks"]["https://github.com/example/hook"]["semver_levels"]["patch"] == "2026-09-17T00:00:00+00:00"
    assert tracking["hooks"]["https://github.com/example/hook"]["semver_levels"]["major"] == "old"
    assert "candidate_updates" not in tracking["hooks"]["https://github.com/example/hook"]