# Use the add-pr-to-projects reusable workflow

Use this workflow when a pull request is opened and you want to add it to one or more `datasciencecampus` Projects, then set a field value (for example `Status = In review`).

Workflow being called:

- `.github/workflows/add-pr-to-projects.yml` in this repository

## Prerequisites

1. The calling repository can use workflows from `datasciencecampus/github-actions`.
2. Organization credentials are available to this workflow:
   - `PROJECT_HANDLER_BOT_APP_ID` (variable)
   - `PROJECT_HANDLER_BOT_PEM` (secret)
3. Each target project and field exists in `datasciencecampus` Projects.

## Add a caller workflow

Create a workflow in your repository:

```yaml
name: Add PRs to org projects

on:
  pull_request:
    types: [opened]

permissions:
  contents: read
  pull-requests: read
  repository-projects: write

jobs:
  add-pr-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-pr-to-projects.yml@main
    with:
      project_field_values: |
        [
          {"project": 194, "field": "Status", "value": "In review"}
        ]
      pull_request_node_id: ${{ github.event.pull_request.node_id }}
```

## Mapping input

Pass a list of dictionaries in `project_field_values`.

Each entry should include:

- `project`: numeric project number
- `field`: project field name
- `value`: value to set for that field

Example entry:

- `{"project": 194, "field": "Status", "value": "In review"}`

## Manual test

Use this repository's test workflow:

- `.github/workflows/test-add-pr-to-projects.yml`

For manual runs, pass both:

- `project_field_values`
- `pull_request_node_id` (if not running from a pull request event)