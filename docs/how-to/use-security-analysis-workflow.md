# Use security-analysis

Automatically scan GitHub Actions workflows with `zizmor` and infrastructure-as-code with `checkov` to identify security misconfigurations.

Reusable workflow: `.github/workflows/security-analysis.yml`

## What it does

- **zizmor**: Scans GitHub Actions workflows for security best practices (shell injection, self-hosted runners, secrets misuse, etc.)
- **checkov**: Scans infrastructure-as-code, configuration files, and YAML for compliance violations
- **SARIF upload**: Uploads results to GitHub Advanced Security (auto-enabled for public repositories)

Both tools run in parallel on every push to `main` and pull request against `main`.

## Prerequisites

No organization-level credentials required. The workflows use the default `GITHUB_TOKEN` with appropriate scoped permissions.

> [!NOTE]
> GitHub Advanced Security (SARIF upload) requires GitHub Advanced Security to be enabled in your repository. For public repositories, SARIF upload is enabled by default.

## Add to your repository

Add a security analysis workflow to your repository's `.github/workflows/` directory:

### Option 1: Default configuration

Use organization defaults (zizmor persona: `auditor`, all checks enabled):

```yaml
name: Security Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

run-name: "${{ github.workflow }} - ${{ github.actor }} - ${{ github.event_name == 'pull_request' && format('PR #{0}', github.event.pull_request.number) || github.ref_name }}"

permissions: {} # Deny token access by default; jobs grant only what they need.

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  security-analysis:
    name: security-analysis
    permissions:
      actions: read # Required for SARIF upload metadata lookups in private or internal repositories.
      contents: read # Required to read repository contents during analysis.
      security-events: write # Required to upload security analysis results.
    uses: datasciencecampus/github-actions/.github/workflows/security-analysis.yml@<COMMIT-SHA> # VERSION NO
```

The top-level `permissions: {}` denies `GITHUB_TOKEN` access by default. The reusable-workflow job then grants only the permissions the analysis needs: `actions: read` for SARIF metadata lookups, `contents: read` to scan repository content, and `security-events: write` to upload SARIF results. Use the same permission declarations with the custom configuration below.

### Option 2: Custom configuration

To customize config paths, persona, or advanced-security behavior:

```yaml
name: Security Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-analysis:
    uses: datasciencecampus/github-actions/.github/workflows/security-analysis.yml@<commit-sha>
    with:
      zizmor-config: ./config/zizmor-custom.yaml
      zizmor-persona: pedantic
      checkov-config: ./config/checkov-custom.yml
      advanced-security: false  # Disable SARIF upload for private testing
```

## Configuration

### Organization config files

Both tools use organization-managed default config files:

- **zizmor**: `datasciencecampus/github-actions:./configs/zizmor.yaml`
- **checkov**: `datasciencecampus/github-actions:./configs/checkov.yml`

To customize, create your own config files in your repository and reference them via `zizmor-config` and `checkov-config` inputs.

### zizmor personas

The `zizmor-persona` input controls analysis strictness:

- `regular`: Standard checks
- `pedantic`: Additional checks for edge cases
- `auditor`: Most comprehensive, recommended for security audits (default)

### Advanced Security behavior

The `advanced-security` input controls SARIF upload:

- **Not specified** (default): Auto-detect based on repository type — enable for public repos, disable for private repos
- **true**: Always upload SARIF results to GitHub Advanced Security
- **false**: Never upload SARIF results

> [!NOTE]
> The `security-analysis.yml` orchestrator implements tri-state logic to maintain backward compatibility. When called from push/PR events, it auto-detects based on repository privacy. When called via `workflow_call`, it respects the caller's explicit override while auto-detecting if the input is omitted.

## Example customizations

### Strict security scanning in private repo

```yaml
with:
  zizmor-persona: auditor
  advanced-security: true  # Force SARIF upload despite private repo
```

### Disable checkov only

Create a custom checkov config that skips all checks, and pass it:

```yaml
with:
  checkov-config: ./config/checkov-disabled.yml
```

Example `./config/checkov-disabled.yml`:

```yaml
# Skip all checks by using an empty framework list
# See https://www.checkov.io/2.Concepts/Suppressing%20Checks/Baseline
framework: []
```

Alternatively, suppress specific checks via framework configuration instead of disabling the entire tool.

### Workflow_dispatch for manual runs

Allow manual runs with custom parameters:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      zizmor-persona:
        description: Analysis persona
        required: false
        type: choice
        options:
          - regular
          - pedantic
          - auditor
        default: auditor

jobs:
  security-analysis:
    uses: datasciencecampus/github-actions/.github/workflows/security-analysis.yml@<commit-sha>
    with:
      zizmor-persona: ${{ github.event.inputs.zizmor-persona || 'auditor' }}
```

## Viewing results

### GitHub Advanced Security tab

SARIF results appear in your repository's **Security** tab under **Code scanning**:

1. Go to your repository
2. Click **Security**
3. Click **Code scanning**
4. View alerts by tool (zizmor, checkov)

### Workflow run logs

Check the workflow run for detailed output:

1. Go to your repository
2. Click **Actions**
3. Find the **Security Analysis** run
4. Click to view full output and logs

## SHA pinning

If your organization requires SHA pinning for reusable workflows, pin the commit SHA:

```yaml
uses: datasciencecampus/github-actions/.github/workflows/security-analysis.yml@<commit-sha>
```

Example:

```yaml
uses: datasciencecampus/github-actions/.github/workflows/security-analysis.yml@a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

## Troubleshooting

### SARIF upload fails

**Issue**: "Upload SARIF file" step fails with permission error.

**Solution**: Ensure the workflow has `security-events: write` permission. Check that GitHub Advanced Security is enabled in your repository settings.

### Checkov config not found

**Issue**: Checkov fails with "Config file not found" error.

**Solution**: Verify the path in `checkov-config` is correct and relative to your repository root.

### Too many zizmor warnings

**Issue**: Too many zizmor findings in `auditor` persona.

**Solution**: Switch to `regular` persona, or create a custom zizmor config to suppress specific checks.

## Related workflows

- [add-issue-to-projects](use-add-issue-to-projects-workflow.md)
- [add-pr-to-projects](use-add-pr-to-projects-workflow.md)
