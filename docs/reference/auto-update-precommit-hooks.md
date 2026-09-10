# Auto-Update Pre-Commit Hooks Reference

Complete reference for the auto-update pre-commit hooks workflow.

## Workflow Metadata

| Property | Value |
|----------|-------|
| **Workflow file** | `.github/workflows/auto-update-precommit-hooks.yml` |
| **Type** | Standalone workflow (not reusable) |
| **Triggers** | `workflow_dispatch` (manual), `schedule` (weekly Tuesday 03:00 UTC) |
| **Permissions** | `contents: write`, `pull-requests: write` |

## Inputs (workflow_dispatch only)

### `cooldown_major_days`

**Description**: Cooldown period (in days) before updating pre-commit hooks to a new major version.

**Type**: `string`  
**Default**: `"28"`  
**Required**: No  
**Example**: `"14"` to reduce from 28 to 14 days

**Rationale**: Major version updates may introduce breaking changes. A longer cooldown period allows time for upstream testing and community feedback before adoption.

---

### `cooldown_minor_days`

**Description**: Cooldown period (in days) before updating pre-commit hooks to a new minor version.

**Type**: `string`  
**Default**: `"14"`  
**Required**: No  
**Example**: `"7"` to reduce from 14 to 7 days

**Rationale**: Minor versions introduce new features and may have minor breaking changes. A moderate cooldown balances freshness with stability.

---

### `cooldown_patch_days`

**Description**: Cooldown period (in days) before updating pre-commit hooks to a new patch version.

**Type**: `string`  
**Default**: `"7"`  
**Required**: No  
**Example**: `"3"` to reduce from 7 to 3 days

**Rationale**: Patch versions are bug fixes and security updates. A shorter cooldown is acceptable for patches, but 7 days is recommended for supply chain attack mitigation.

---

### `skip_hooks`

**Description**: Comma-separated list of pre-commit hook repository URLs to skip during this run.

**Type**: `string`  
**Default**: `""` (empty string; no hooks skipped)  
**Required**: No  
**Example**: `"https://github.com/zizmorcore/zizmor-pre-commit,https://github.com/other/hook"`

**Rationale**: Allows temporary exclusion of specific hooks from auto-updates without modifying configuration files.

---

### `force_update`

**Description**: Bypass all cooldown periods and update all eligible hooks immediately.

**Type**: `boolean`  
**Default**: `false`  
**Required**: No  
**Example**: `true`

**⚠️ Security Note**: Enabling this increases exposure to supply chain attacks by bypassing the recommended cooldown periods. Use only when necessary and with careful review.

---

## Job Outputs

### `detect-updates`

**`updates_found`**
- Type: `string` (`"true"` or `"false"`)
- Description: Whether any updates were detected in the configured pre-commit hooks

**`updates_json`**
- Type: `string` (JSON-encoded array)
- Description: Array of detected updates with structure:
  ```json
  [
    {
      "repo": "https://github.com/zizmorcore/zizmor-pre-commit",
      "old_sha": "451b56af716f9f0d0c2b816503a3fd0cf8b036fa",
      "new_sha": "abc123def456...",
      "old_version": "v1.29.0",
      "new_version": "v1.30.0",
      "semver_level": "minor",
      "commit_range": "451b56af716f9f0d0c2b816503a3fd0cf8b036fa...abc123def456"
    }
  ]
  ```

---

### `apply-cooldown`

**`eligible_updates`**
- Type: `string` (JSON-encoded array)
- Description: Updates that passed the cooldown filter, same structure as `detect-updates.updates_json` plus `cooldown_applied` field

**`skipped_updates`**
- Type: `string` (JSON-encoded array)
- Description: Updates that were filtered out due to active cooldown, with additional fields:
  - `reason`: Human-readable reason (e.g., "Cooldown active: 3/28 days")
  - `days_remaining`: Number of days until cooldown expires

---

### `fetch-release-info`

**`release_info`**
- Type: `string` (JSON-encoded array)
- Description: Eligible updates enriched with release notes and commit information:
  ```json
  [
    {
      "repo": "https://github.com/zizmorcore/zizmor-pre-commit",
      "old_sha": "451b56af716f9f0d0c2b816503a3fd0cf8b036fa",
      "new_sha": "abc123def456...",
      "old_version": "v1.29.0",
      "new_version": "v1.30.0",
      "semver_level": "minor",
      "commit_range": "451b56af716f9f0d0c2b816503a3fd0cf8b036fa...abc123def456",
      "release_notes": "## v1.30.0\n\n### Features\n- Added feature X\n\n### Fixes\n- Fixed bug Y",
      "commits": ["abc123def456...", "def456ghi789..."],
      "commit_count": 2
    }
  ]
  ```

---

## Configuration Files

### `configs/precommit-update-tracking.json`

**Schema**:

```json
{
  "last_updated": "2026-09-10T12:34:56Z",
  "hooks": {
    "{repo_url}": {
      "last_updated": "2026-09-10T12:34:56Z",
      "current_sha": "{40-char-sha}",
      "current_version": "{semantic-version-tag}",
      "semver_levels": {
        "major": "2026-07-15T10:00:00Z",
        "minor": "2026-08-20T14:30:00Z",
        "patch": "2026-09-08T09:15:00Z"
      }
    }
  }
}
```

**Field Descriptions**:

- `last_updated`: ISO-8601 timestamp of the last workflow update to this file
- `hooks[{repo_url}].last_updated`: Last time this specific hook was updated
- `hooks[{repo_url}].current_sha`: Current commit SHA for this hook (40 characters)
- `hooks[{repo_url}].current_version`: Semantic version tag (e.g., `v1.29.0`)
- `hooks[{repo_url}].semver_levels.{level}`: ISO-8601 timestamp of the last update at this semver level
  - `major`: Last major version update
  - `minor`: Last minor version update
  - `patch`: Last patch version update

**Initialization**: The workflow initializes this file on first run using hooks from `.pre-commit-config.yaml`.

**Persistence**: Updated automatically by the workflow after creating a PR.

---

### `configs/precommit-updates-config.json`

**Schema**:

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

**Field Descriptions**:

- `cooldown_days.major`: Default cooldown period for major version updates (days)
- `cooldown_days.minor`: Default cooldown period for minor version updates (days)
- `cooldown_days.patch`: Default cooldown period for patch version updates (days)
- `hooks_to_skip`: Array of hook repository URLs to exclude from auto-updates
- `enable_auto_updates`: Global flag to enable/disable auto-updates (currently informational; not enforced by workflow)

**Precedence**: Workflow input parameters override these defaults when provided.

**Manual editing**: You can edit this file directly to change defaults or add hooks to the skip list.

---

## Pull Request Body Format

The workflow generates pull requests with this markdown structure:

```markdown
## Summary

{github.actor} ran on {YYYY-MM-DD HH:MM:SS UTC} and updated {N} hook(s).

**Workflow run**: [{RUN_ID}]({RUN_URL})

---

## Changes

### {hook_name} `[{SEMVER_LEVEL}]`
`{old_version}` → `{new_version}`

<details><summary>Commits ({count})</summary>

\`\`\`
- {commit_sha_short}
...
\`\`\`

[View commit history]({repo_url}/compare/{old_sha_short}...{new_sha_short})

</details>

<details><summary>Release Notes</summary>

{release_notes_text}

</details>

---

## Risks & Notes

### ⚠️ Major Version Updates (if applicable)
Major versions may introduce breaking changes...

### ⚠️ Short Cooldown Period (if applicable)
Cooldown periods less than 7 days increase vulnerability...

### Cooldown Periods Applied
- **Major versions**: {N} days
- **Minor versions**: {N} days
- **Patch versions**: {N} days

### Skipped Updates (if any)
The following updates are available but skipped...
```

---

## Behavior by Event

### `workflow_dispatch` (Manual Trigger)

1. Detects available updates
2. Applies cooldown filters (respecting input overrides)
3. Fetches release notes and commit history
4. Updates `.pre-commit-config.yaml` and `precommit-update-tracking.json`
5. Creates a PR on the `main` branch from a feature branch

**Branch naming**: `chore/precommit-updates-{YYYYMMDD}`

**PR title**: `chore(pre-commit): auto-update hooks ({N} update(s))`

**Commit author**: `github-actions[bot]` (41898282+github-actions[bot]@users.noreply.github.com)

---

### `schedule` (Automatic Weekly Run)

Runs at **Tuesday 03:00 UTC** using default cooldown periods.

- Input: `cooldown_major_days=28`, `cooldown_minor_days=14`, `cooldown_patch_days=7`
- Actor: Workflow (no explicit user)
- Honors all skip lists and configurations

---

## Semver Level Detection

The workflow determines update severity using semantic versioning:

| From | To | Level | Default Cooldown |
|------|----|----|------------------|
| v1.2.3 | v2.0.0 | **MAJOR** | 28 days |
| v1.2.3 | v1.3.0 | **MINOR** | 14 days |
| v1.2.3 | v1.2.4 | **PATCH** | 7 days |
| {sha} | {new_sha} | **PATCH** | 7 days (if no tag) |

If the workflow cannot parse a version (e.g., no release tag), it defaults to `PATCH` level.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No updates found | Job `no-updates` runs; logs message and exits successfully |
| GitHub API limit exceeded | Workflow logs warning and continues with fallback data |
| Release notes unavailable | Logs "(No release notes available)"; PR still created |
| Commit history fetch fails | Uses short commit SHAs; PR still created |
| PR creation fails | Workflow fails with error message; manual PR creation may be needed |
| Concurrent runs (race condition) | Later run may have git push conflicts; manual intervention needed |

---

## Permissions Required

| Permission | Scope | Why |
|-----------|-------|-----|
| `contents: write` | Repository | To commit and push updates to `.pre-commit-config.yaml` |
| `pull-requests: write` | Repository | To create pull requests |
| `GITHUB_TOKEN` | API | To fetch release information and commit history (automatic) |

---

## Frequently Asked Questions

### Q: Why does the workflow show "No updates found" even though I see a new release?

**A**: Possible reasons:
1. The new release was published less than the configured cooldown period ago
2. The hook is in the `hooks_to_skip` list
3. The upstream repository doesn't publish releases; check if commit history is being used instead

Check `configs/precommit-update-tracking.json` for the last update timestamp per semver level.

---

### Q: Can I manually edit `precommit-update-tracking.json` to reset cooldowns?

**A**: Yes. Edit the `semver_levels.{level}` timestamp to an earlier date to make updates available immediately. For example, set `"major": "2020-01-01T00:00:00Z"` to reset the major version cooldown.

---

### Q: What if I want to skip a hook permanently?

**A**: Add the hook URL to `configs/precommit-updates-config.json`:

```json
"hooks_to_skip": ["https://github.com/zizmorcore/zizmor-pre-commit"]
```

Or pass `skip_hooks` during manual trigger.

---

### Q: What if a PR is created but the branch push fails?

**A**: Check for:
1. Branch protection rules that block pushes
2. Concurrent workflow runs (race condition)
3. Repository access permissions

Manual push of the branch and PR creation may be needed.

---

## See Also

- [How to Use the Auto-Update Workflow](../how-to/use-auto-update-precommit-hooks-workflow.md)
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) — Your repository's hooks
- [Pre-commit Documentation](https://pre-commit.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
