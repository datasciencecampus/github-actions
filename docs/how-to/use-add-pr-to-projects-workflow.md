# Use add-pr-to-projects

Adds a pull request to one or more `datasciencecampus` ProjectsV2 boards and sets a field value (for example `Status = Review`).

Workflow: `.github/workflows/add-pr-to-projects.yml`

## Prerequisites

The following organisation-level Actions variables and secrets must be available to your repository:

- `PROJECT_ROUTER_BOT_APP_ID`: variable containing the client ID of the app that triggers the workflow.
- `PROJECT_ROUTER_BOT_PEM`: secret containing the private key of the app that triggers the workflow.

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
    runs-on: ubuntu-latest
    steps:
      - name: Create GitHub App token for dispatch
        id: app-token
        uses: actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1 # v3.2.0
        with:
          client-id: ${{ vars.PROJECT_ROUTER_BOT_APP_ID }}
          private-key: ${{ secrets.PROJECT_ROUTER_BOT_PEM }}
          owner: datasciencecampus
          repositories: github-actions
          permission-actions: write

      - name: Dispatch add-pr-to-projects workflow
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          PROJECT_FIELD_VALUES: '[{"project":194,"field":"Status","value":"Review"}]'
          PULL_REQUEST_NODE_ID: ${{ github.event.pull_request.node_id }}
          REPOSITORY_NAME: ${{ github.event.repository.name }}
          REF: ${{ github.head_ref }}
        run: |
          jq -n \
            --arg ref "$REF" \
            --arg repo "$REPOSITORY_NAME" \
            --arg node_id "$PULL_REQUEST_NODE_ID" \
            --arg project_field_values "$PROJECT_FIELD_VALUES" \
            '{
              ref: $ref,
              inputs: {
                repository: $repo,
                pull_request_node_id: $node_id,
                project_field_values: $project_field_values
              }
            }' | curl -sS -L --fail-with-body \
              -X POST \
              -H "Accept: application/vnd.github+json" \
              -H "Authorization: Bearer ${GH_TOKEN}" \
              https://api.github.com/repos/datasciencecampus/github-actions/actions/workflows/add-pr-to-projects.yml/dispatches \
              -d @-
```

## Input format

`project_field_values` is a JSON array. Each entry must have:

- `project`: required. Numeric project number.
- `field`: required. Field name in the project.
- `value`: required. Value to set for that field.

Example — set Status to Review on project 194:

```json
[{ "project": 194, "field": "Status", "value": "Review" }]
```

Example — set fields on two projects:

```json
[
  { "project": 194, "field": "Status", "value": "Review" },
  { "project": 205, "field": "Priority", "value": "High" }
]
```

## Finding your project number

Your project number appears in the URL of the project board:
`https://github.com/orgs/datasciencecampus/projects/194` → project number is `194`.

## Security checks performed by the called workflow

Before the pull request is added to a project, the central workflow will:

1. Verify that the submitted pull request node ID resolves to the named repository.
2. Refuse requests that claim an organization other than `datasciencecampus`.

These checks are enforced in the called workflow, so changing the caller YAML does not bypass them.
