"""Enrich eligible updates with upstream release context."""

from __future__ import annotations

from typing import Any

from .github import GitHubClient
from .models import is_sha_like_version


def enrich_updates(updates: list[dict[str, Any]], github: GitHubClient) -> list[dict[str, Any]]:
    """Add release notes and bounded commit information to updates.

    Args:
        updates: Eligible update records containing repository and SHA fields.
        github: Client used to query release metadata.

    Returns:
        New update records with release notes, commit SHAs, and commit counts.
    """
    enriched: list[dict[str, Any]] = []
    for update in updates:
        tag = update["new_version"]
        release_notes = None if is_sha_like_version(tag) else github.release_notes(update["repo"], tag)
        comparison = github.comparison(update["repo"], update["old_sha"], update["new_sha"])
        enriched.append(
            {
                **update,
                "release_notes": release_notes or "(No release notes available)",
                "commits": comparison.commits,
                "commit_count": comparison.total_commits,
            }
        )
    return enriched