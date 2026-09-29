# Reusable workflows reference

This page lists the workflows in this repository and their caller-facing contracts.

## Project workflow credentials

Callers of the project-routing workflows use these credentials to dispatch the internal implementations:

- `PROJECT_ROUTER_BOT_APP_ID` (Actions variable, org-level)
- `PROJECT_ROUTER_BOT_PRIVATE_KEY` (Actions secret, org-level)

> [!IMPORTANT]
> For public caller repositories that run these workflows automatically on issue or pull request creation events, those events must be limited to trusted actors. In practice, require collaborator-only issue or pull request creation, or an equivalent repository control. Configure this in the caller repository at `https://github.com/<owner>/<repo>/settings` under `Settings > General > Features`, then use `Issues > Issue permissions` or `Pull requests > Pull request permissions` as appropriate.

Project-handling credentials are used internally and are not required from callers. The project workflows verify that the requested organization matches this repository owner and that the submitted issue or pull request node ID resolves back to the repository named in the request. See [GitHub Apps reference](github-apps.md).

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

- `zizmor-config`: optional string. Path to zizmor config file in the caller's checkout. Defaults to `./configs/zizmor.yaml`.
- `zizmor-persona`: optional string. Persona for zizmor analysis: `regular`, `pedantic`, or `auditor`. Defaults to `auditor`.
- `checkov-config`: optional string. Path to checkov config file in the caller's checkout. Defaults to `./configs/checkov.yml`.
- `advanced-security`: optional boolean. Upload SARIF results to GitHub Advanced Security. Tri-state behavior:
  - Omitted (default): Auto-detect based on repository privacy (true for public, false for private)
  - `true`: Always upload
  - `false`: Never upload

### Security Analysis Behavior

1. Runs `zizmor` to scan GitHub Actions workflows for security misconfigurations.
2. Runs `checkov` to scan infrastructure-as-code and configuration files.
3. Both tools run in parallel and upload SARIF results to GitHub Advanced Security (when enabled).
4. Reads config files from the caller's checkout at the configured paths.

### Security Analysis Notes

- **Default triggers**: On this repository's `push` and `pull_request` events for `main`, the config files in this repository are used (zizmor persona: `auditor`, both tools enabled). Callers using `workflow_call` must provide the config files in their own checkout or set the config path inputs.
- **Customization**: Callers can override config paths, persona, and advanced-security via `workflow_call` inputs.
- **Tri-state logic**: `advanced-security` input is tri-state (omit = auto-detect, true = enable, false = disable). This logic is computed by the orchestrator and passed to child workflows.
- **Concurrency**: Managed at the orchestrator level to prevent duplicate runs.
- **Child workflows**: `zizmor.yml` and `checkov.yml` expose `workflow_call` and can be called directly, but callers should use `security-analysis.yml` to run both tools with the shared trigger, concurrency, and SARIF policy.

## terraform-quality

Workflow file: `.github/workflows/terraform-quality.yml`

### Terraform Quality Trigger

`workflow_call` only.

### Terraform Quality Inputs

- `terraform-dirs`: optional JSON array of repository-relative directories to validate. Defaults to the four standard environment directories. Input validation rejects non-arrays, non-string entries, empty paths, absolute paths, and paths containing `..`.
- `terraform-version`: optional string. Terraform version to install. Defaults to `1.14.3`.
- `run-fmt`: optional boolean. Run the Terraform formatting check. Defaults to `true`.
- `run-validate`: optional boolean. Run `terraform init -backend=false` and `terraform validate` for each configured directory. Defaults to `true`.
- `run-tflint`: optional boolean. Run TFLint. Defaults to `true`.
- `continue_on_error`: optional boolean intended for negative testing. Defaults to `false`; when enabled, failures in the validation checks do not fail the workflow.

### Terraform Quality Behavior

1. Validates the `terraform-dirs` input before running checks.
2. Runs `terraform fmt -check -recursive terraform` when formatting is enabled.
3. Runs `terraform init -backend=false` and `terraform validate` for each configured directory when validation is enabled.
4. Runs TFLint recursively under `terraform/` when enabled, using `configs/.tflint.hcl` from the caller's checkout.

### Terraform Quality Notes

- `terraform-dirs` controls only `terraform validate`; formatting and TFLint scan the entire `terraform/` directory.
- The caller must provide `configs/.tflint.hcl` when TFLint is enabled.
- The workflow exposes a `validation-passed` output indicating whether `terraform-dirs` input validation succeeded.

### Terraform Quality `GITHUB_TOKEN` Permissions

- `contents: read`

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
