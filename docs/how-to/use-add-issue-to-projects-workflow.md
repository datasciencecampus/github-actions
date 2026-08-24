# Use the add-issue-to-projects reusable workflow

Use this workflow when you want newly opened issues to be added to one or more `datasciencecampus` Projects.

Workflow being called:

- `.github/workflows/add-issue-to-projects.yml` in this repository

## Prerequisites

1. The calling repository can use workflows from `datasciencecampus/github-actions`.
2. Organization credentials are available to this workflow:
   - `PROJECT_HANDLER_BOT_APP_ID` (variable)
   - `PROJECT_HANDLER_BOT_PEM` (secret)
3. Project numbers already exist in the `datasciencecampus` org.

## Add a caller workflow

Create a workflow in your repository:

```yaml
name: Add issues to org projects

on:
  issues:
    types: [opened]

permissions:
  contents: read
  issues: read
  repository-projects: write

jobs:
  add-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@main
    with:
      project_numbers: |
        194
        205
```

## Manual test

Use this repository's test workflow:

- `.github/workflows/test-add-issue-to-projects.yml`

Run it with `workflow_dispatch` and provide `project_numbers`.

## Input format

- `project_numbers` accepts comma-separated values or newline-separated values.
- Only numeric project numbers are allowed.

Examples:

- `194,205`
- multiline block with one project number per line