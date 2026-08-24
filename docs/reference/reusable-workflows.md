# Reusable workflows reference

This page lists the workflows in this repository and their caller-facing contracts.

## Shared credential model

Authorized callers use the dispatch credentials to trigger workflows:

- `PROJECT_ROUTER_BOT_APP_ID` (Actions variable, org-level)
- `PROJECT_ROUTER_BOT_PRIVATE_KEY` (Actions secret, org-level)

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
- It is most useful for workflows in this repository, or same-organization callers that intentionally expose the dispatch secret to the called workflow.

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
