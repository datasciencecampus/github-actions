# How to Use the Auto-Update Pre-Commit Hooks Workflow

This guide explains how to use the auto-update pre-commit hooks workflow to keep your pre-commit hooks up-to-date with minimal manual effort.

## Overview

The auto-update workflow:
- Detects new releases for pre-commit hooks defined in `.pre-commit-config.yaml`
- Applies semver-based cooldown periods to prevent overly frequent updates
- Creates informative pull requests with release summaries and risk assessments
- Can run on a schedule or be called from another workflow

## Quick Start

### Automatic Scheduled Updates

Add a scheduled caller workflow to run the reusable workflow automatically, for example every Tuesday at 03:00 UTC.

To view scheduled runs, navigate to:
```
GitHub Repository → Actions → Auto-Update Pre-Commit Hooks
```

### Reusable Workflow Trigger

To call the workflow from another repository:

```yaml
name: Auto-Update Pre-Commit Hooks

on:
  schedule:
    - cron: "0 3 * * 2"

permissions: {}

jobs:
  update-precommit-hooks:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/github-actions/.github/workflows/auto-update-precommit-hooks.yml@<commit-sha>
```

## Workflow Options

When calling with `workflow_call`, you can customize the behavior:

### Cooldown Periods

The workflow respects semver-based cooldown periods measured from the candidate release publication time:

| Level | Default Cooldown | Purpose |
|-------|------------------|---------|
| **Major** | 28 days | Major updates may introduce breaking changes; longer wait allows time for upstream testing |
| **Minor** | 14 days | New features; moderate risk of breaking changes |
| **Patch** | 7 days | Bug fixes; low risk, important for security |

To override cooldown periods in a caller workflow:

```yaml
jobs:
  update-precommit-hooks:
    permissions:
      contents: write
      pull-requests: write
    uses: datasciencecampus/github-actions/.github/workflows/auto-update-precommit-hooks.yml@<commit-sha>
    with:
      cooldown_major_days: "14"
      cooldown_minor_days: "7"
      cooldown_patch_days: "3"
```

### Force Update

To bypass all cooldown periods and update all eligible hooks immediately:

```yaml
with:
  force_update: true
```

**⚠️ Use with caution**: Bypassing cooldown periods increases exposure to supply chain attacks.

### Skip Specific Hooks

To exclude specific pre-commit hooks from being updated:

```yaml
with:
  skip_hooks: "https://github.com/zizmorcore/zizmor-pre-commit,https://github.com/other/hook"
```

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

Tracks the current SHA, version, and local adoption timestamps for each hook. This file is automatically created and updated by the workflow.

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

Cooldowns are based on the candidate release publication timestamp, so editing local adoption timestamps does not reset the waiting period.

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
1. **Cooldown period active**: Check the workflow summary to see how recently the candidate release was published
2. **Hook is in skip list**: Check `skip_hooks` input or `configs/precommit-updates-config.json`
3. **No releases available**: The upstream repository may not use GitHub releases. The workflow falls back to checking commits.

To force an update:
- Call the workflow with `force_update: true`

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

### Bypass Cooldown for a Single Run

Set `force_update: true` in the caller workflow for an urgent run. Remove the override after use so future releases follow the configured waiting period.

## See Also

- [Auto-Update Pre-Commit Hooks Reference](../reference/auto-update-precommit-hooks.md) — detailed input/output contract
- [.pre-commit-config.yaml](.pre-commit-config.yaml) — your repository's pre-commit hooks
