# Reusable workflows reference

This page lists the workflows in this repository and their caller-facing contracts.

## Shared credential model

Callers use the router bot credentials to dispatch workflows:

- `PROJECT_ROUTER_BOT_APP_ID` (Actions variable, org-level)
- `PROJECT_ROUTER_BOT_PEM` (Actions secret, org-level)

Project-handling credentials are used internally and are not required from callers. See [GitHub Apps reference](github-apps.md).

## add-issue-to-projects

Workflow file: `.github/workflows/add-issue-to-projects.yml`

### Trigger

`workflow_dispatch` via `POST /repos/datasciencecampus/github-actions/actions/workflows/add-issue-to-projects.yml/dispatches`

### Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `issue_node_id` | Yes | Node ID of the issue to add |
| `project_field_values` | Yes | JSON array of project mappings (see below) |
| `repository` | No | Source repository name for token scoping |
| `organization` | No | Organization login; defaults to repository owner |

### project_field_values format

Each entry must have `project`. `field` and `value` are optional — if omitted the issue is added with no field update.

```json
[{"project": 194}]
[{"project": 194, "field": "Status", "value": "Backlog"}]
```

### Behavior

1. Validates credentials.
2. Parses and validates all mapping entries.
3. For each entry: adds the issue to the project if not already present.
4. If `field` is specified: sets the field value on the project item.

### GITHUB_TOKEN permissions

- `contents: read`

---

## add-pr-to-projects

Workflow file: `.github/workflows/add-pr-to-projects.yml`

### Trigger

`workflow_dispatch` via `POST /repos/datasciencecampus/github-actions/actions/workflows/add-pr-to-projects.yml/dispatches`

### Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `pull_request_node_id` | Yes | Node ID of the pull request to add |
| `project_field_values` | Yes | JSON array of project mappings (see below) |
| `repository` | No | Source repository name for token scoping |
| `organization` | No | Organization login; defaults to repository owner |

### project_field_values format

Each entry must have `project`, `field`, and `value`.

```json
[{"project": 194, "field": "Status", "value": "Review"}]
```

### Behavior

1. Validates credentials.
2. Parses and validates all mapping entries (project, field, and value required).
3. For each entry: adds the pull request to the project if not already present.
4. Sets the configured field value on the project item.

### GITHUB_TOKEN permissions

- `contents: read`
- `pull-requests: read`

