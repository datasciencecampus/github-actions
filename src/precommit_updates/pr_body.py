"""Render the review body for an automated hook-update pull request."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any


def extract_hook_name(repo_url: str) -> str:
    """Extract the final repository component from a URL.

    Args:
        repo_url: Repository URL or fallback display value.

    Returns:
        Repository name without a trailing ``.git`` suffix when present.
    """
    match = re.search(r"/([^/]+?)(?:\.git)?$", repo_url)
    return match.group(1) if match else repo_url


def generate_pr_body(
    updates: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    cooldown_config: dict[str, int],
    *,
    force_update: bool = False,
    actor: str = "Workflow",
    run_id: str = "local",
    repository: str = "unknown",
    server_url: str = "https://github.com",
    now: datetime | None = None,
) -> str:
    """Render the markdown body for an update pull request.

    Args:
        updates: Applied update records and optional release context.
        skipped: Updates excluded by policy.
        cooldown_config: Cooldown durations shown in the policy summary.
        force_update: Whether the force-update warning is included.
        actor: Workflow actor shown in the summary.
        run_id: GitHub Actions run identifier.
        repository: Full GitHub repository name.
        server_url: GitHub server base URL.
        now: Optional timestamp used for deterministic rendering.

    Returns:
        Markdown suitable for the pull request body.
    """
    now = now or datetime.now(timezone.utc)
    lines = ["## Summary", "", f"{actor} ran on {now.strftime('%Y-%m-%d %H:%M:%S UTC')} and updated **{len(updates)} hook(s)**.", "", f"**Workflow run**: [{run_id}]({server_url}/{repository}/actions/runs/{run_id})", "", "---", "", "## Changes", ""]

    for update in updates:
        level = update.get("semver_level", "unknown").upper()
        lines.extend([f"### {extract_hook_name(update['repo'])} `[{level}]`", f"`{update['old_version']}` -> `{update['new_version']}`", ""])
        commits = update.get("commits", [])
        if commits:
            lines.extend([f"<details><summary>Commits ({update.get('commit_count', len(commits))})</summary>", "", "```"])
            lines.extend(f"- {commit[:7]}" for commit in commits[:10])
            lines.extend(["```", "", f"[View commit history]({update['repo']}/compare/{update['old_sha'][:7]}...{update['new_sha'][:7]})", "", "</details>", ""])
        notes = update.get("release_notes", "(No release notes)")
        if notes and notes != "(No release notes available)":
            lines.extend(
                [
                    "<details><summary>Release Notes</summary>",
                    "",
                    html.escape(notes, quote=False),
                    "",
                    "</details>",
                    "",
                ]
            )

    lines.extend(["---", "", "## Risks & Notes", ""])
    if any(update.get("semver_level") == "major" for update in updates):
        lines.extend(["> [!WARNING]", "> Major Version Updates", ">", "> Major versions may introduce breaking changes. Reviewers should examine the release notes and commit history carefully.", ""])
    if any(update.get("cooldown_applied", {}).get(update.get("semver_level"), 0) < 7 for update in updates):
        lines.extend(["> [!WARNING]", "> Short Cooldown Period", ">", "> Some updates have cooldown periods less than 7 days, which may increase vulnerability to supply chain attacks.", ""])
    if force_update:
        lines.extend(["### Update Policy", "", "> [!NOTE]", "> **Force Update Override**", ">", "> Cooldown periods were bypassed via `force_update: true`.", ""])
    else:
        lines.extend(["### Cooldown Periods Applied", "", f"- **Major versions**: {cooldown_config['major']} days", f"- **Minor versions**: {cooldown_config['minor']} days", f"- **Patch versions**: {cooldown_config['patch']} days", ""])
    if skipped:
        lines.extend(["### Skipped Updates", "", "The following updates are available but skipped due to policy:", ""])
        lines.extend(f"- **{extract_hook_name(update['repo'])}**: {update.get('reason', 'Policy filtered') }" for update in skipped)
    return "\n".join(lines)