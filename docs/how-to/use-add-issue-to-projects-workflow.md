# Use add-issue-to-projects

Adds an issue to one or more `datasciencecampus` ProjectsV2 boards and optionally sets a field value (for example `Status = Backlog`).

If no field is specified, the issue is added to the project without any field update — useful for simple triage boards.

Reusable workflow: `.github/workflows/add-issue-to-projects.yml`

Internal implementation: `.github/workflows/add-issue-to-projects-impl.yml`

## Prerequisites

Same organisation-level credentials as `add-pr-to-projects` — see [Prerequisites](use-add-pr-to-projects-workflow.md#prerequisites).

> [!IMPORTANT]
> If the calling repository is public and triggers this workflow automatically from `issues` events, it must restrict issue creation to collaborators only, or apply an equivalent control that ensures those events come only from trusted actors. Configure this in the caller repository at `https://github.com/<owner>/<repo>/settings` under `Settings > General > Features > Issues > Issue permissions`.

The project-handling credentials are stored in this repository and require no action from callers.

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
    uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@<commit-sha>
    secrets:
      PROJECT_ROUTER_BOT_PRIVATE_KEY: ${{ secrets.PROJECT_ROUTER_BOT_PRIVATE_KEY }}
    with:
      repository: ${{ github.event.repository.name }}
      issue_node_id: ${{ github.event.issue.node_id }}
      project_field_values: '[{"project":1234}]'
```

If your organisation requires SHA pinning, pin the reusable workflow with `@<commit-sha>`. When `implementation_ref` is omitted, the called workflow dispatches the release-managed tag recorded in the pinned workflow revision.

## Input format

`project_field_values` is a JSON array. Each entry must have a `project` number. `field` and `value` are optional. If omitted, the issue is added without any field update.

- `project`: required. Numeric project number.
- `field`: optional. Field name in the project.
- `value`: optional, but required if `field` is provided. Value to set for that field.

Example — add to project with no field update:

```json
[{ "project": 1234 }]
```

Example — add to project and set Status:

```json
[{ "project": 1234, "field": "Status", "value": "Backlog" }]
```

Example — two projects, one with a field update:

```json
[
  { "project": 1234 },
  { "project": 5678, "field": "Priority", "value": "Medium" }
]
```

## Finding your project number

Your project number appears in the URL of the project board:
`https://github.com/orgs/datasciencecampus/projects/1234` → project number is `1234`.

## Security checks performed by the called workflow

Before the issue is added to a project, the internal implementation workflow will:

1. Verify that the submitted issue node ID resolves to the named repository.
2. Refuse requests that claim an organization other than `datasciencecampus`.

These checks are enforced in the called workflow, so changing the caller YAML does not bypass them.
