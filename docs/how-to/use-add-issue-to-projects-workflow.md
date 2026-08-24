# Use add-issue-to-projects via repository_dispatch

Use this workflow when you want newly opened issues to be added to one or more `datasciencecampus` Projects.

Workflow:

- `.github/workflows/add-issue-to-projects.yml` in this repository

## Prerequisites

1. The caller can send `repository_dispatch` to `datasciencecampus/github-actions`.
2. Organization credentials are available to this workflow:
  - `PROJECT_HANDLER_BOT_APP_ID` (variable)
  - `PROJECT_HANDLER_BOT_PEM` (secret)
3. Project numbers already exist in the `datasciencecampus` org.

## Trigger this repo via repository_dispatch

Use this repository's test workflow for manual dispatch checks:

- `.github/workflows/test-add-issue-to-projects.yml`

## Input format

- `project_numbers` accepts comma-separated values or newline-separated values.
- Only numeric project numbers are allowed.

Examples:

- `194,205`
- multiline block with one project number per line

## Trigger this repo via repository_dispatch

If you want execution to happen in `datasciencecampus/github-actions` (for example to use its environment secrets), trigger this workflow with a repository dispatch event.

Example using GitHub CLI:

```bash
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/datasciencecampus/github-actions/dispatches \
  -f event_type='add-issue-to-projects' \
  -f client_payload='{
    "repository":"my-caller-repo",
    "issue_node_id":"I_kwDOExample",
    "project_numbers":"194,205"
  }'
```

Dispatch payload fields:

- `project_numbers` (required): comma-separated or newline-separated project numbers
- `issue_node_id` (required): issue node id
- `repository` (optional): source repository name for token scoping