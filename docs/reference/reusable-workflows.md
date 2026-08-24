# Reusable workflows reference

This page lists the reusable workflows in this repository and their caller-facing contracts.

## Shared credential model

These called workflows use org-scoped credentials inside the called workflow:

- `PROJECT_HANDLER_BOT_APP_ID` (Actions variable)
- `PROJECT_HANDLER_BOT_PEM` (Actions secret)

Dispatch caller workflows should use router bot credentials to send repository dispatch events:

- `PROJECT_ROUTER_BOT_APP_ID` (Actions variable)
- `PROJECT_ROUTER_BOT_PEM` (Actions secret)

## add-issue-to-projects

Workflow file:

- `.github/workflows/add-issue-to-projects.yml`

### add-issue-to-projects trigger contract

- `repository_dispatch` with event type `add-issue-to-projects`

### add-issue-to-projects payload fields

For `repository_dispatch`, pass values in `client_payload`:

- `project_numbers` (required): comma-separated or newline-separated project numbers
- `issue_node_id` (required): issue node id
- `repository` (optional): source repository name for token scoping. If omitted, defaults to this repository name.

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

- `repository_dispatch` with event type `add-pr-to-projects`

### add-pr-to-projects payload fields

For `repository_dispatch`, pass values in `client_payload`:

- `project_field_values` (required): JSON string list of mappings
- `pull_request_node_id` (required): pull request node id
- `repository` (optional): source repository name for token scoping. If omitted, defaults to this repository name.

### add-pr-to-projects behavior

1. Validates credentials.
2. Validates all mapping entries (project, field, value).
3. Adds the pull request to each target project if needed.
4. Sets the configured field value on each created/found project item.

### add-pr-to-projects permissions used

- `contents: read`
- `pull-requests: read`
- `repository-projects: write`
