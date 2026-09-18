from datetime import datetime, timezone, timedelta

import pytest

from precommit_updates.models import CooldownConfig
from precommit_updates.policy import filter_updates


NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)
UPDATE = {
    "repo": "https://github.com/example/hook",
    "semver_level": "patch",
    "candidate_published_at": (NOW - timedelta(days=7)).isoformat(),
}


def tracking_at(days_ago: int) -> dict:
    timestamp = (NOW - timedelta(days=days_ago)).isoformat()
    return {"hooks": {UPDATE["repo"]: {"semver_levels": {"patch": timestamp}}}}


def test_cooldown_skips_before_boundary_and_allows_at_boundary():
    config = CooldownConfig(patch=7)
    recent_update = {**UPDATE, "candidate_published_at": (NOW - timedelta(days=6)).isoformat()}
    eligible, skipped = filter_updates([recent_update], tracking_at(365), config, now=NOW)
    assert not eligible
    assert skipped[0]["days_remaining"] == 1

    eligible, skipped = filter_updates([UPDATE], tracking_at(0), config, now=NOW)
    assert len(eligible) == 1
    assert not skipped


def test_skip_list_precedes_force_update():
    eligible, skipped = filter_updates(
        [UPDATE], {}, CooldownConfig(), now=NOW, force_update=True, skip_hooks=[UPDATE["repo"]]
    )
    assert not eligible
    assert skipped[0]["reason"] == "Hook in skip list"


def test_force_update_bypasses_cooldown():
    eligible, skipped = filter_updates(
        [UPDATE], tracking_at(0), CooldownConfig(), now=NOW, force_update=True
    )
    assert len(eligible) == 1
    assert not skipped


def test_unknown_level_and_invalid_timestamp_are_skipped():
    unknown = {"repo": "unknown", "semver_level": "unknown"}
    malformed = {**UPDATE, "candidate_published_at": "not-a-date"}
    missing = {"repo": UPDATE["repo"], "semver_level": "patch"}
    tracking = {"hooks": {UPDATE["repo"]: {"semver_levels": {"patch": "not-a-date"}}}}
    eligible, skipped = filter_updates([unknown, malformed, missing], tracking, CooldownConfig(), now=NOW)
    assert not eligible
    assert [item["reason"] for item in skipped] == [
        "Unsupported semantic version level",
        "Invalid candidate published timestamp",
        "Missing candidate published timestamp",
    ]


def test_local_update_timestamp_does_not_make_new_release_eligible():
    recent_release = {**UPDATE, "candidate_published_at": (NOW - timedelta(days=1)).isoformat()}
    old_local_update = tracking_at(365)

    eligible, skipped = filter_updates([recent_release], old_local_update, CooldownConfig(), now=NOW)

    assert not eligible
    assert skipped[0]["reason"] == "Cooldown active: 1/7 days"


def test_now_must_be_timezone_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        filter_updates([UPDATE], {}, CooldownConfig(), now=datetime(2026, 9, 17))