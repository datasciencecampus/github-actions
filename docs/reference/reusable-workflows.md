# Reusable workflows reference

This page lists the reusable workflows in this repository and their caller-facing contracts.

## Shared credential model

These workflows use org-scoped credentials inside the called workflow:

- `PROJECT_HANDLER_BOT_APP_ID` (Actions variable)
- `PROJECT_HANDLER_BOT_PEM` (Actions secret)

Callers do not pass through secrets.

## add-issue-to-projects

Workflow file:

- `.github/workflows/add-issue-to-projects.yml`

### add-issue-to-projects trigger contract

- `workflow_call`

### add-issue-to-projects inputs

- `project_numbers` (required, string)
  - Comma-separated or newline-separated project numbers
  - Example: `194,205`

### add-issue-to-projects behavior

1. Validates credentials.
2. Validates and normalizes project numbers.
3. Verifies project numbers exist in `datasciencecampus` Projects.
4. Adds the issue to each target project.

### add-issue-to-projects permissions used

- `contents: read`
- `issues: read`
- `repository-projects: write`

## add-pr-to-projects

Workflow file:

- `.github/workflows/add-pr-to-projects.yml`

### add-pr-to-projects trigger contract

- `workflow_call`

### add-pr-to-projects inputs

- `project_field_values` (required, string)
  - A list of mappings: project, field, value
  - Recommended format: JSON array string
  - Example:
    - `[{"project":194,"field":"Status","value":"In review"}]`
- `pull_request_node_id` (optional, string)
  - If omitted, read from event payload

### add-pr-to-projects behavior

1. Validates credentials.
2. Validates all mapping entries (project, field, value).
3. Adds the pull request to each target project if needed.
4. Sets the configured field value on each created/found project item.

### add-pr-to-projects permissions used

- `contents: read`
- `pull-requests: read`
- `repository-projects: write`
