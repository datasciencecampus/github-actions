"""Discover commit-pinned pre-commit hook updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .github import GitHubClient
from .models import determine_semver_level


def detect_updates(
    config_path: Path,
    tracking_path: Path,
    github: GitHubClient,
) -> list[dict[str, Any]]:
    """Return available tagged-release updates for configured hooks.

    Args:
        config_path: Path to the commit-pinned pre-commit configuration.
        tracking_path: Path to durable update tracking state.
        github: Client used to query upstream releases and tags.

    Returns:
        Update records containing old/new SHAs, versions, semver level, and range.
    """
    with config_path.open() as config_file:
        config = yaml.safe_load(config_file) or {}

    tracking_data: dict[str, Any] = {}
    if tracking_path.exists():
        with tracking_path.open() as tracking_file:
            tracking_data = json.load(tracking_file).get("hooks", {})

    updates: list[dict[str, Any]] = []
    for repo_entry in config.get("repos", []):
        repo_url = repo_entry.get("repo")
        current_sha = repo_entry.get("rev")
        if not repo_url or not current_sha:
            continue

        release_info = github.latest_release(repo_url)
        if not release_info:
            continue
        latest_tag, latest_sha, candidate_published_at = release_info
        if latest_sha == current_sha:
            continue

        old_version = tracking_data.get(repo_url, {}).get("current_version")
        if not old_version:
            old_version = github.tag_for_sha(repo_url, current_sha)
        old_version = old_version or current_sha[:7]
        if old_version == latest_tag:
            continue

        updates.append(
            {
                "repo": repo_url,
                "old_sha": current_sha,
                "new_sha": latest_sha,
                "old_version": old_version,
                "new_version": latest_tag,
                "candidate_published_at": candidate_published_at,
                "semver_level": determine_semver_level(old_version, latest_tag),
                "commit_range": f"{current_sha}...{latest_sha}",
            }
        )
    return updates