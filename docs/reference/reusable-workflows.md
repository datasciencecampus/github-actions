# Reusable workflows reference

This page lists the workflows in this repository and their caller-facing contracts.

## Shared credential model

Authorized callers use the dispatch credentials to trigger workflows:

- `PROJECT_ROUTER_BOT_APP_ID` (Actions variable, org-level)
- `PROJECT_ROUTER_BOT_PRIVATE_KEY` (Actions secret, org-level)

> [!IMPORTANT]
> For public caller repositories that run these workflows automatically on issue or pull request creation events, those events must be limited to trusted actors. In practice, require collaborator-only issue or pull request creation, or an equivalent repository control. Configure this in the caller repository at `https://github.com/<owner>/<repo>/settings` under `Settings > General > Features`, then use `Issues > Issue permissions` or `Pull requests > Pull request permissions` as appropriate.

Project-handling credentials are used internally and are not required from callers. The called workflows verify that the requested organization matches this repository owner and that the submitted issue or pull request node ID resolves back to the repository named in the request. See [GitHub Apps reference](github-apps.md).

## add-issue-to-projects

Workflow file: `.github/workflows/add-issue-to-projects.yml`

### Issue Call Trigger

`workflow_call`

### Issue Call Inputs

- `implementation_ref`: optional override. Branch or tag ref to use when dispatching `.github/workflows/add-issue-to-projects-impl.yml`.
- `repository`: required. Source repository name.
- `issue_node_id`: required. Node ID of the issue to add.
- `project_field_values`: required. JSON array of project mappings.
- `organization`: optional compatibility field; if provided it is forwarded to the implementation workflow.

### Issue Call Behavior

1. Validates the dispatch credentials and required dispatch inputs.
2. Mints a dispatch token with `actions: write` on `datasciencecampus/github-actions`.
3. Dispatches `.github/workflows/add-issue-to-projects-impl.yml` with the supplied inputs.

### Issue Call Notes

- This is the public reusable workflow for the issue flow.
- If `implementation_ref` is omitted, the workflow reads `configs/implementation-ref.json` from the invoked workflow revision, turns `implementation_version` into a `v...` tag, and dispatches that release-managed ref.
- Use `implementation_ref` only to override that release-managed dispatch target with a specific branch or tag.
- It is most useful for workflows in this repository, or same-organization callers that intentionally provide the dispatch secret to the public reusable workflow.

### Issue Self-Test Workflow

- `.github/workflows/test-add-issue-to-projects-reusable.yml` manually exercises this reusable workflow with `workflow_dispatch` inputs.
- The same test workflow also runs automatically on `issues.opened` in this repository.
- For automatic runs, it derives `project_field_values` from the repository Actions variable `PROJECT_NUMBER`.

## add-issue-to-projects-impl

Workflow file: `.github/workflows/add-issue-to-projects-impl.yml`

### Issue Trigger

`workflow_dispatch` via `POST /repos/datasciencecampus/github-actions/actions/workflows/add-issue-to-projects-impl.yml/dispatches`

### Issue Inputs

- `issue_node_id`: required. Node ID of the issue to add.
- `project_field_values`: required. JSON array of project mappings.
- `repository`: required. Source repository name.
- `organization`: optional compatibility field; if provided it must match the owner of this repository.

### Issue `project_field_values` Format

Each entry must have `project`. `field` and `value` are optional — if omitted the issue is added with no field update.

```json
[{"project": 1234}]
[{"project": 1234, "field": "Status", "value": "Backlog"}]
```

### Issue Behavior

1. Validates credentials.
2. Verifies that the submitted issue node ID belongs to the named source repository.
3. Parses and validates all mapping entries.
4. For each entry: adds the issue to the project if not already present.
5. If `field` is specified: sets the field value on the project item.

### Issue `GITHUB_TOKEN` Permissions

- `contents: read`

---

## add-pr-to-projects

Workflow file: `.github/workflows/add-pr-to-projects.yml`

### Pull Request Call Trigger

`workflow_call`

### Pull Request Call Inputs

- `implementation_ref`: optional override. Branch or tag ref to use when dispatching `.github/workflows/add-pr-to-projects-impl.yml`.
- `repository`: required. Source repository name.
- `pull_request_node_id`: required. Node ID of the pull request to add.
- `project_field_values`: required. JSON array of project mappings.
- `organization`: optional compatibility field; if provided it is forwarded to the implementation workflow.

### Pull Request Call Behavior

1. Validates the dispatch credentials and required dispatch inputs.
2. Mints a dispatch token with `actions: write` on `datasciencecampus/github-actions`.
3. Dispatches `.github/workflows/add-pr-to-projects-impl.yml` with the supplied inputs.

### Pull Request Call Notes

- This is the public reusable workflow for the pull request flow.
- If `implementation_ref` is omitted, the workflow reads `configs/implementation-ref.json` from the invoked workflow revision, turns `implementation_version` into a `v...` tag, and dispatches that release-managed ref.
- Use `implementation_ref` only to override that release-managed dispatch target with a specific branch or tag.

### Pull Request Self-Test Workflow

- `.github/workflows/test-add-pr-to-projects-reusable.yml` manually exercises this reusable workflow with `workflow_dispatch` inputs.
- The same test workflow also runs automatically on `pull_request.opened` and `pull_request.reopened` in this repository.
- For automatic runs, it derives `project_field_values` from the repository Actions variable `PROJECT_NUMBER`, using `Status = Review` as the default field mapping.

## add-pr-to-projects-impl

Workflow file: `.github/workflows/add-pr-to-projects-impl.yml`

### Pull Request Trigger

`workflow_dispatch` via `POST /repos/datasciencecampus/github-actions/actions/workflows/add-pr-to-projects-impl.yml/dispatches`

### Pull Request Inputs

- `pull_request_node_id`: required. Node ID of the pull request to add.
- `project_field_values`: required. JSON array of project mappings.
- `repository`: required. Source repository name.
- `organization`: optional compatibility field; if provided it must match the owner of this repository.

### Pull Request `project_field_values` Format

Each entry must have `project`, `field`, and `value`.

```json
[{ "project": 1234, "field": "Status", "value": "Review" }]
```

### Pull Request Behavior

1. Validates credentials.
2. Verifies that the submitted pull request node ID belongs to the named source repository.
3. Parses and validates all mapping entries (project, field, and value required).
4. For each entry: adds the pull request to the project if not already present.
5. Sets the configured field value on the project item.

### Pull Request `GITHUB_TOKEN` Permissions

- `contents: read`
- `pull-requests: read`

---

## security-analysis

Workflow file: `.github/workflows/security-analysis.yml`

Orchestrates GitHub Actions security analysis with `zizmor` and infrastructure security scanning with `checkov`.

### Security Analysis Triggers

- `push` to `main`
- `pull_request` against `main`
- `workflow_call` (for reuse in other repositories)

### Security Analysis Call Inputs (workflow_call only)

- `zizmor-config`: optional string. Path to zizmor config file. Defaults to `./configs/zizmor.yaml`.
- `zizmor-persona`: optional string. Persona for zizmor analysis: `regular`, `pedantic`, or `auditor`. Defaults to `auditor`.
- `checkov-config`: optional string. Path to checkov config file. Defaults to `./configs/checkov.yml`.
- `advanced-security`: optional boolean. Upload SARIF results to GitHub Advanced Security. Tri-state behavior:
  - Omitted (default): Auto-detect based on repository privacy (true for public, false for private)
  - `true`: Always upload
  - `false`: Never upload

### Security Analysis Behavior

1. Runs `zizmor` to scan GitHub Actions workflows for security misconfigurations.
2. Runs `checkov` to scan infrastructure-as-code and configuration files.
3. Both tools run in parallel and upload SARIF results to GitHub Advanced Security (when enabled).
4. Uses organization-managed config defaults from `./configs/zizmor.yaml` and `./configs/checkov.yml`.

### Security Analysis Notes

- **Default triggers**: On `push` and `pull_request` to `main`, uses organization defaults (zizmor persona: `auditor`, both tools enabled).
- **Customization**: Callers can override config paths, persona, and advanced-security via `workflow_call` inputs.
- **Tri-state logic**: `advanced-security` input is tri-state (omit = auto-detect, true = enable, false = disable). This logic is computed by the orchestrator and passed to child workflows.
- **Concurrency**: Managed at the orchestrator level to prevent duplicate runs.
- **Child workflows**: `zizmor.yml` and `checkov.yml` are internal workflows and should be called only via `security-analysis.yml`.

## zizmor

Workflow file: `.github/workflows/zizmor.yml`

GitHub Actions workflow security scanning using `zizmor`.

### Zizmor Trigger

`workflow_call` only (called by `security-analysis.yml`)

### Zizmor Inputs

- `config-path`: optional string. Path to zizmor config file. Defaults to `./configs/zizmor.yaml`.
- `persona`: optional string. Analysis persona: `regular`, `pedantic`, or `auditor`. Defaults to `auditor`.
- `advanced-security`: optional boolean. Upload SARIF results to GitHub Advanced Security. Defaults to `false`. Callers should pass the tri-state value computed by the orchestrator.

### Zizmor Notes

- This is an internal workflow; call via `security-analysis.yml` instead.
- Tri-state logic (auto-detect based on repository privacy) is implemented in `security-analysis.yml`.

### Zizmor Behavior

1. Checks out the repository.
2. Runs zizmor with the specified config and persona.
3. Uploads SARIF results (when advanced-security is enabled).

### Zizmor `GITHUB_TOKEN` Permissions

- `actions: read`
- `contents: read`
- `security-events: write`

## checkov

Workflow file: `.github/workflows/checkov.yml`

Infrastructure-as-code and configuration security scanning using `checkov`.

### Checkov Trigger

`workflow_call` only (called by `security-analysis.yml`)

### Checkov Inputs

- `config-path`: optional string. Path to checkov config file. Defaults to `./configs/checkov.yml`.
- `advanced-security`: optional boolean. Upload SARIF results to GitHub Advanced Security. Defaults to `false`. Callers should pass the tri-state value computed by the orchestrator.

### Checkov Behavior

1. Checks out the repository.
2. Runs checkov with the specified config file.
3. Outputs results as CLI and SARIF formats.
4. Uploads SARIF results (when advanced-security is enabled).

### Checkov Notes

- This is an internal workflow; call via `security-analysis.yml` instead.
- Tri-state logic (auto-detect based on repository privacy) is implemented in `security-analysis.yml`.

### Checkov `GITHUB_TOKEN` Permissions

- `contents: read`
- `security-events: write`

---

## auto-update-precommit-hooks

Workflow file: `.github/workflows/auto-update-precommit-hooks.yml`

Detects tagged releases for pre-commit hooks in the caller repository, applies cooldown policy using caller configuration, and opens a pull request with the proposed updates.

### Auto-Update Triggers

- `workflow_call` (for reuse in other repositories)
- `schedule` (weekly Tuesday 03:00 UTC in this repository)

### Auto-Update Call Inputs (workflow_call only)

- `cooldown_major_days`: optional string. Cooldown period for major version updates. Overrides `configs/precommit-updates-config.json`; built-in fallback is `"28"`.
- `cooldown_minor_days`: optional string. Cooldown period for minor version updates. Overrides `configs/precommit-updates-config.json`; built-in fallback is `"14"`.
- `cooldown_patch_days`: optional string. Cooldown period for patch version updates. Overrides `configs/precommit-updates-config.json`; built-in fallback is `"7"`.
- `skip_hooks`: optional string. Comma-separated hook repository URLs to skip. Overrides `configs/precommit-updates-config.json` `hooks_to_skip` when provided.
- `force_update`: optional boolean. Bypass cooldown periods and update all eligible hooks. Defaults to `false`.

### Auto-Update Behavior

1. Checks out the caller repository into `caller`.
2. Checks out this repository into `implementation` at the invoked workflow SHA.
3. Installs the Python implementation package from `implementation`.
4. Runs detection, cooldown filtering, release enrichment, and pull request creation from the `caller` workspace.

### Auto-Update Notes

- The caller repository must contain `.pre-commit-config.yaml`.
- The tracking file defaults to `configs/precommit-update-tracking.json` in the caller repository and is initialized by the workflow if missing.
- Persistent defaults are read from `configs/precommit-updates-config.json` in the caller repository when present.
- This workflow does not use the project-routing `implementation_ref` dispatch model.

### Auto-Update `GITHUB_TOKEN` Permissions

- `contents: write`
- `pull-requests: write`
