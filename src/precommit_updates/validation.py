"""Validate pre-commit configuration against update tracking state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def initialize_tracking(config_path: Path, tracking_path: Path) -> None:
    """Create baseline tracking state from configured hook revisions."""
    with config_path.open() as config_file:
        config = yaml.safe_load(config_file) or {}

    tracking = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "hooks": {
            entry["repo"]: {
                "current_sha": entry["rev"],
                "semver_levels": {},
            }
            for entry in config.get("repos", [])
            if entry.get("repo") and entry.get("rev")
        },
    }
    tracking_path.parent.mkdir(parents=True, exist_ok=True)
    with tracking_path.open("w") as tracking_file:
        json.dump(tracking, tracking_file, indent=2)
        tracking_file.write("\n")


def alignment_errors(config_path: Path, tracking_path: Path) -> list[str]:
    """Return errors when configured hooks and tracking state are out of sync.

    Args:
        config_path: Path to the pre-commit configuration.
        tracking_path: Path to the update tracking JSON file.

    Returns:
        Human-readable alignment errors. An empty list means the files align.
    """
    with config_path.open() as config_file:
        config = yaml.safe_load(config_file) or {}
    with tracking_path.open() as tracking_file:
        tracking = json.load(tracking_file)

    configured = {
        entry.get("repo"): entry
        for entry in config.get("repos", [])
        if entry.get("repo") and entry.get("rev")
    }
    tracked: dict[str, Any] = tracking.get("hooks", {})
    errors: list[str] = []

    for repo in sorted(set(configured) - set(tracked)):
        errors.append(f"missing tracking entry: {repo}")
    for repo in sorted(set(tracked) - set(configured)):
        errors.append(f"extra tracking entry: {repo}")
    for repo in sorted(set(configured) & set(tracked)):
        configured_sha = configured[repo]["rev"]
        tracked_sha = tracked[repo].get("current_sha")
        if configured_sha != tracked_sha:
            errors.append(f"SHA mismatch for {repo}: config={configured_sha}, tracking={tracked_sha}")

    return errors