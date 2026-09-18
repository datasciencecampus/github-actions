"""Discover commit-pinned pre-commit hook updates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .github import GitHubClient
from .models import determine_semver_level


def detect_updates(
    config_path: Path,
    tracking_path: Path,
    github: GitHubClient,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return available tagged-release updates for configured hooks.

    Args:
        config_path: Path to the commit-pinned pre-commit configuration.
        tracking_path: Path to durable update tracking state.
        github: Client used to query upstream releases and tags.
        now: Timestamp used when first observing candidate updates.

    Returns:
        Update records containing old/new SHAs, versions, semver level, and range.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    with config_path.open() as config_file:
        config = yaml.safe_load(config_file) or {}

    tracking: dict[str, Any] = {"hooks": {}}
    if tracking_path.exists():
        with tracking_path.open() as tracking_file:
            tracking = json.load(tracking_file)
    hooks = tracking.setdefault("hooks", {})

    updates: list[dict[str, Any]] = []
    tracking_changed = False
    for repo_entry in config.get("repos", []):
        repo_url = repo_entry.get("repo")
        current_sha = repo_entry.get("rev")
        if not repo_url or not current_sha:
            continue

        tag_info = github.latest_tag(repo_url)
        if not tag_info:
            continue
        latest_tag, latest_sha = tag_info
        if latest_sha == current_sha:
            continue

        hook_tracking = hooks.setdefault(repo_url, {})
        old_version = hook_tracking.get("current_version")
        if not old_version:
            old_version = github.tag_for_sha(repo_url, current_sha)
        old_version = old_version or current_sha[:7]
        if old_version == latest_tag:
            continue
        semver_level = determine_semver_level(old_version, latest_tag)

        if semver_level == "unknown":
            continue

        first_seen_at, candidate_changed = _candidate_first_seen_at(
            hook_tracking,
            tag=latest_tag,
            sha=latest_sha,
            now=now,
        )
        tracking_changed = tracking_changed or candidate_changed

        updates.append(
            {
                "repo": repo_url,
                "old_sha": current_sha,
                "new_sha": latest_sha,
                "old_version": old_version,
                "new_version": latest_tag,
                "candidate_first_seen_at": first_seen_at,
                "semver_level": semver_level,
                "commit_range": f"{current_sha}...{latest_sha}",
            }
        )
    if tracking_changed:
        tracking["last_checked"] = now.isoformat()
        with tracking_path.open("w") as tracking_file:
            json.dump(tracking, tracking_file, indent=2)
            tracking_file.write("\n")
    return updates


def _candidate_first_seen_at(
    hook_tracking: dict[str, Any],
    *,
    tag: str,
    sha: str,
    now: datetime,
) -> tuple[str, bool]:
    """Return and persist the first time a candidate tag/SHA was observed."""
    candidates = hook_tracking.setdefault("candidate_updates", {})
    candidate = candidates.get(tag)
    if isinstance(candidate, dict) and candidate.get("sha") == sha and candidate.get("first_seen_at"):
        return str(candidate["first_seen_at"]), False

    candidates[tag] = {"sha": sha, "first_seen_at": now.isoformat()}
    return now.isoformat(), True