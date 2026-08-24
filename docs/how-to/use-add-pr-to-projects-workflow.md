# Use add-pr-to-projects

Adds a pull request to one or more `datasciencecampus` ProjectsV2 boards and sets a field value (for example `Status = Review`).

Reusable workflow: `.github/workflows/add-pr-to-projects.yml`

Internal implementation: `.github/workflows/add-pr-to-projects-impl.yml`

## Prerequisites

The calling repository must be provisioned with the required router-bot Actions variable and secret:

- `PROJECT_ROUTER_BOT_APP_ID`: variable containing the client ID of the app that triggers the workflow.
- `PROJECT_ROUTER_BOT_PRIVATE_KEY`: secret containing the private key of the app that triggers the workflow.

The project-handling credentials are stored in this repository and require no action from callers.

## Add to your repository

Create `.github/workflows/add-pr-to-projects.yml` in your repository with the following content.
Replace the `project_field_values` string with your own configuration (see [Input format](#input-format) below).

```yaml
name: Add Pull Request To Projects

on:
  pull_request:
    types: [opened, reopened]

permissions:
  contents: read

jobs:
  add-pr-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-pr-to-projects.yml@<commit-sha>
    secrets:
      PROJECT_ROUTER_BOT_PRIVATE_KEY: ${{ secrets.PROJECT_ROUTER_BOT_PRIVATE_KEY }}
    with:
      repository: ${{ github.event.repository.name }}
      pull_request_node_id: ${{ github.event.pull_request.node_id }}
      project_field_values: '[{"project":1234,"field":"Status","value":"Review"}]'
```

If your organisation requires SHA pinning, pin the reusable workflow with `@<commit-sha>` and omit `implementation_ref` unless you need to override the release-managed version recorded in the pinned workflow revision.

## Input format

`project_field_values` is a JSON array. Each entry must have:

- `project`: required. Numeric project number.
- `field`: required. Field name in the project.
- `value`: required. Value to set for that field.

Example — set Status to Review on a project:

```json
[{ "project": 1234, "field": "Status", "value": "Review" }]
```

Example — set fields on two projects:

```json
[
  { "project": 1234, "field": "Status", "value": "Review" },
  { "project": 5678, "field": "Priority", "value": "High" }
]
```

## Finding your project number

Your project number appears in the URL of the project board:
`https://github.com/orgs/datasciencecampus/projects/1234` → project number is `1234`.

## Security checks performed by the called workflow

Before the pull request is added to a project, the internal implementation workflow will:

1. Verify that the submitted pull request node ID resolves to the named repository.
2. Refuse requests that claim an organization other than `datasciencecampus`.

These checks are enforced in the called workflow, so changing the caller YAML does not bypass them.
