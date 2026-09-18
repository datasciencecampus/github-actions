"""Cooldown and skip-list policy for detected updates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .models import CooldownConfig, SEMVER_LEVELS


def filter_updates(
    updates: Iterable[dict[str, Any]],
    tracking: dict[str, Any],
    cooldown: CooldownConfig,
    *,
    now: datetime,
    force_update: bool = False,
    skip_hooks: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply skip-list, force-update, and cooldown policy.

    Args:
        updates: Candidate update records.
        tracking: Durable state keyed by repository URL.
        cooldown: Validated cooldown durations.
        now: Time against which cooldown timestamps are evaluated.
        force_update: Whether to bypass cooldown timestamps.
        skip_hooks: Repository URLs excluded even during forced updates.

    Returns:
        A pair of eligible records and skipped records with human-readable reasons.

    Raises:
        ValueError: If ``now`` is timezone-naive.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    skipped_repos = set(skip_hooks)
    eligible: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for update in updates:
        repo = update["repo"]
        if repo in skipped_repos:
            skipped.append({**update, "reason": "Hook in skip list"})
            continue

        level = update.get("semver_level")
        if level not in SEMVER_LEVELS:
            skipped.append({**update, "reason": "Unsupported semantic version level"})
            continue

        if not force_update:
            timestamp = update.get("candidate_published_at")
            if not timestamp:
                skipped.append({**update, "reason": "Missing candidate published timestamp"})
                continue
            try:
                candidate_published = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if candidate_published.tzinfo is None:
                    raise ValueError("timestamp must be timezone-aware")
            except (AttributeError, TypeError, ValueError):
                skipped.append({**update, "reason": "Invalid candidate published timestamp"})
                continue

            elapsed_days = (now.astimezone(timezone.utc) - candidate_published.astimezone(timezone.utc)).days
            required_days = cooldown.for_level(level)
            if elapsed_days < required_days:
                skipped.append(
                    {
                        **update,
                        "reason": f"Cooldown active: {elapsed_days}/{required_days} days",
                        "days_remaining": required_days - elapsed_days,
                    }
                )
                continue

        eligible.append({**update, "cooldown_applied": cooldown.as_dict()})

    return eligible, skipped