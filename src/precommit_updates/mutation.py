"""Apply approved update data to repository configuration and tracking state."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


def apply_updates(
    config_path: Path,
    tracking_path: Path,
    updates: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> None:
    """Update hook revisions and durable tracking state in place.

    Args:
        config_path: Path to the YAML pre-commit configuration.
        tracking_path: Path to the JSON tracking state.
        updates: Enriched update records to apply.
        now: Optional timezone-aware timestamp used for tracking fields.

    Raises:
        ValueError: If ``now`` is timezone-naive.
        OSError: If either input or output file cannot be accessed.
        json.JSONDecodeError: If existing tracking state is invalid JSON.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    with config_path.open() as config_file:
        config = yaml.load(config_file)

    if tracking_path.exists():
        with tracking_path.open() as tracking_file:
            tracking = json.load(tracking_file)
    else:
        tracking = {"last_updated": now.isoformat(), "hooks": {}}
    tracking.setdefault("hooks", {})

    update_map = {update["repo"]: update for update in updates}
    timestamp = now.isoformat()
    for repo_entry in config.get("repos", []):
        repo_url = repo_entry.get("repo")
        update = update_map.get(repo_url)
        if not update:
            continue

        repo_entry["rev"] = update["new_sha"]
        if hasattr(repo_entry, "ca"):
            repo_entry.yaml_add_eol_comment(
                f'frozen: {update["new_version"]}', key="rev"
            )

        hook = tracking["hooks"].setdefault(
            repo_url,
            {
                "current_sha": update["new_sha"],
                "current_version": update["new_version"],
                "semver_levels": {level: timestamp for level in ("major", "minor", "patch")},
            },
        )
        hook["current_sha"] = update["new_sha"]
        hook["current_version"] = update["new_version"]
        hook.setdefault("semver_levels", {})
        level = update.get("semver_level")
        if level in ("major", "minor", "patch"):
            hook["semver_levels"][level] = timestamp
        hook.pop("candidate_updates", None)
        hook["last_updated"] = timestamp

    tracking["last_updated"] = timestamp
    with config_path.open("w") as config_file:
        yaml.dump(config, config_file)
    with tracking_path.open("w") as tracking_file:
        json.dump(tracking, tracking_file, indent=2)
        tracking_file.write("\n")