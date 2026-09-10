# How to Use the Auto-Update Pre-Commit Hooks Workflow

This guide explains how to use the auto-update pre-commit hooks workflow to keep your pre-commit hooks up-to-date with minimal manual effort.

## Overview

The auto-update workflow:
- Detects new releases for pre-commit hooks defined in `.pre-commit-config.yaml`
- Applies semver-based cooldown periods to prevent overly frequent updates
- Creates informative pull requests with release summaries and risk assessments
- Can run on a schedule or be triggered manually

## Quick Start

### Automatic Scheduled Updates

The workflow runs automatically every Tuesday at 03:00 UTC. No action needed.

To view scheduled runs, navigate to:
```
GitHub Repository → Actions → Auto-Update Pre-Commit Hooks
```

### Manual Trigger

To manually trigger the workflow:

1. Go to **Actions** tab in your GitHub repository
2. Select **Auto-Update Pre-Commit Hooks** workflow
3. Click **Run workflow**
4. Choose your options (see below) and click **Run workflow**

## Workflow Options

When manually triggering with `workflow_dispatch`, you can customize the behavior:

### Cooldown Periods

The workflow respects semver-based cooldown periods to balance freshness with stability:

| Level | Default Cooldown | Purpose |
|-------|------------------|---------|
| **Major** | 28 days | Major updates may introduce breaking changes; longer wait allows time for upstream testing |
| **Minor** | 14 days | New features; moderate risk of breaking changes |
| **Patch** | 7 days | Bug fixes; low risk, important for security |

To override cooldown periods in a manual run:

1. In the **Run workflow** dialog:
   - Set **Cooldown period for major version updates (days)**: e.g., `14` to reduce from default 28
   - Set **Cooldown period for minor version updates (days)**: e.g., `7`
   - Set **Cooldown period for patch version updates (days)**: e.g., `3`

2. Click **Run workflow**

### Force Update

To bypass all cooldown periods and update all eligible hooks immediately:

1. In the **Run workflow** dialog, enable **Bypass cooldown periods and update all eligible hooks**
2. Click **Run workflow**

**⚠️ Use with caution**: Bypassing cooldown periods increases exposure to supply chain attacks.

### Skip Specific Hooks

To exclude specific pre-commit hooks from being updated:

1. In the **Run workflow** dialog, set **Comma-separated list of hook repo URLs to skip**
   - Example: `https://github.com/zizmorcore/zizmor-pre-commit,https://github.com/other/hook`
2. Click **Run workflow**

## Understanding the Pull Request

When the workflow detects updates, it creates a pull request with this structure:

### Summary Section

Shows who triggered the update, when it ran, and how many hooks were updated:

```
alice ran on 2026-09-10 12:34:56 UTC and updated 2 hooks.

Workflow run: [12345](https://github.com/...)
```

### Changes Section

Lists each updated hook with version information:

```
### hook-name [MAJOR]
v1.2.3 → v2.0.0

<details><summary>Commits (5)</summary>
...
</details>

<details><summary>Release Notes</summary>
...
</details>
```

The **Commits** section (collapsible) shows the commits between the old and new versions. Click to expand.

The **Release Notes** section (collapsible) shows the upstream release notes. Click to expand.

### Risks & Notes Section

Highlights potential concerns:

- **Major Version Updates**: Warning if any hook has a major version bump
- **Short Cooldown Period**: Warning if cooldown < 7 days (increases supply chain attack risk)
- **Cooldown Periods Applied**: Summary of the cooldown periods used
- **Skipped Updates**: Lists any updates that were available but skipped due to active cooldown

## Configuration Files

### `configs/precommit-update-tracking.json`

Tracks the last update timestamp and semver levels for each hook. This file is automatically created and updated by the workflow.

**Manual inspection example:**

```json
{
  "last_updated": "2026-09-10T12:34:56Z",
  "hooks": {
    "https://github.com/zizmorcore/zizmor-pre-commit": {
      "last_updated": "2026-09-10T12:34:56Z",
      "current_sha": "abc123...",
      "current_version": "v1.29.0",
      "semver_levels": {
        "major": "2026-07-15T10:00:00Z",
        "minor": "2026-08-20T14:30:00Z",
        "patch": "2026-09-08T09:15:00Z"
      }
    }
  }
}
```

To manually reset a hook's cooldown, edit `semver_levels.{level}` to an earlier date.

### `configs/precommit-updates-config.json`

Stores default configuration for the workflow:

```json
{
  "cooldown_days": {
    "major": 28,
    "minor": 14,
    "patch": 7
  },
  "hooks_to_skip": [],
  "enable_auto_updates": true
}
```

**Note**: Workflow input parameters take precedence over this file.

## Reviewing and Merging Updates

1. When a PR is created by the workflow, review the changes:
   - Inspect the release notes (click to expand)
   - Check the commit history (click to expand)
   - Note any warnings in the **Risks & Notes** section

2. For major version updates:
   - Read the release notes carefully
   - Check for any breaking changes
   - Test locally if concerned: `pre-commit run --all-files`

3. Merge the PR once satisfied with the changes

## Troubleshooting

### Workflow Run Shows "No Updates Found"

This means all pre-commit hooks are on their latest versions, or all available updates are still in cooldown periods. This is expected behavior.

### A Specific Hook Never Updates

Possible reasons:
1. **Cooldown period active**: Check `configs/precommit-update-tracking.json` to see when the last update occurred
2. **Hook is in skip list**: Check `skip_hooks` input or `configs/precommit-updates-config.json`
3. **No releases available**: The upstream repository may not use GitHub releases. The workflow falls back to checking commits.

To force an update:
- Manually trigger the workflow with **Bypass cooldown periods and update all eligible hooks** enabled

### Workflow Fails with "Could Not Fetch Latest Release"

The workflow falls back to fetching the latest commit if GitHub releases are unavailable. This is normal and the workflow should still complete successfully.

## Advanced: Manual Configuration

### Temporarily Skip a Hook

Edit `configs/precommit-updates-config.json` and add the hook URL to `hooks_to_skip`:

```json
{
  "hooks_to_skip": ["https://github.com/zizmorcore/zizmor-pre-commit"]
}
```

Then commit and push. The next workflow run will skip that hook.

### Reset Cooldown for a Single Hook

Edit `configs/precommit-update-tracking.json` and set the desired `semver_levels.{level}` to an old date (e.g., `2020-01-01T00:00:00Z`):

```json
"semver_levels": {
  "major": "2020-01-01T00:00:00Z",
  "minor": "2026-09-10T12:34:56Z",
  "patch": "2026-09-10T12:34:56Z"
}
```

Commit and push, then trigger the workflow.

## See Also

- [Auto-Update Pre-Commit Hooks Reference](../reference/auto-update-precommit-hooks.md) — detailed input/output contract
- [.pre-commit-config.yaml](.pre-commit-config.yaml) — your repository's pre-commit hooks
