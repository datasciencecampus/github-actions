# Use add-issue-to-projects

Adds an issue to one or more `datasciencecampus` ProjectsV2 boards and optionally sets a field value (for example `Status = Backlog`).

If no field is specified, the issue is added to the project without any field update — useful for simple triage boards.

Workflow: `.github/workflows/add-issue-to-projects.yml`

## Prerequisites

Same organisation-level credentials as `add-pr-to-projects` — see [Prerequisites](use-add-pr-to-projects-workflow.md#prerequisites).

The project-handling credentials are stored in this repository and require no action from callers.

Your repository must also be added to the central allowlist in this repository, and each project number you intend to target must be approved for that repository. Use the access request form in [.github/ISSUE_TEMPLATE/request-github-token-access.yml](../../.github/ISSUE_TEMPLATE/request-github-token-access.yml) when onboarding a new repository or project.

## Add to your repository

Create `.github/workflows/add-issue-to-projects.yml` in your repository with the following content.
Replace the `project_field_values` string with your own configuration (see [Input format](#input-format) below).

```yaml
name: Add Issue To Projects

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read

jobs:
  add-issue-to-projects:
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

      - name: Dispatch add-issue-to-projects workflow
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          PROJECT_FIELD_VALUES: '[{"project":194}]'
          ISSUE_NODE_ID: ${{ github.event.issue.node_id }}
          REPOSITORY_NAME: ${{ github.event.repository.name }}
          REF: ${{ github.ref_name }}
        run: |
          jq -n \
            --arg ref "$REF" \
            --arg repo "$REPOSITORY_NAME" \
            --arg node_id "$ISSUE_NODE_ID" \
            --arg project_field_values "$PROJECT_FIELD_VALUES" \
            '{
              ref: $ref,
              inputs: {
                repository: $repo,
                issue_node_id: $node_id,
                project_field_values: $project_field_values
              }
            }' | curl -sS -L --fail-with-body \
              -X POST \
              -H "Accept: application/vnd.github+json" \
              -H "Authorization: Bearer ${GH_TOKEN}" \
              https://api.github.com/repos/datasciencecampus/github-actions/actions/workflows/add-issue-to-projects.yml/dispatches \
              -d @-
```

## Input format

`project_field_values` is a JSON array. Each entry must have a `project` number. `field` and `value` are optional. If omitted, the issue is added without any field update.

- `project`: required. Numeric project number.
- `field`: optional. Field name in the project.
- `value`: optional, but required if `field` is provided. Value to set for that field.

Example — add to project with no field update:

```json
[{ "project": 194 }]
```

Example — add to project and set Status:

```json
[{ "project": 194, "field": "Status", "value": "Backlog" }]
```

Example — two projects, one with a field update:

```json
[{ "project": 194 }, { "project": 205, "field": "Priority", "value": "Medium" }]
```

## Finding your project number

Your project number appears in the URL of the project board:
`https://github.com/orgs/datasciencecampus/projects/194` → project number is `194`.

## Security checks performed by the called workflow

Before the issue is added to a project, the central workflow will:

1. Refuse requests from repositories that are not on the central allowlist.
2. Refuse project numbers that are not approved for the calling repository.
3. Verify that the submitted issue node ID resolves to the approved repository.

These checks are enforced in the called workflow, so changing the caller YAML does not bypass them.
