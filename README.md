# github-actions

Reusable workflows for the Data Science Campus GitHub organization.

This repository is the sister repository to [ONSdigital/ons-github-actions](https://github.com/ONSdigital/ons-github-actions).

- `ONSdigital/ons-github-actions` contains reusable workflows that are broadly applicable.
- This repository contains Data Science Campus org-specific workflows that require organization-scoped variables, secrets, or app credentials.

Example org-specific use case:

- [Add issue to projects](.github/workflows/add-issue-to-projects.yml), which requires org-scoped GitHub App credentials to add issue items to `datasciencecampus` Projects.

## Pre-commit hook (zizmor)

This repository includes a pre-commit hook configuration for `zizmor` in [.pre-commit-config.yaml](.pre-commit-config.yaml).

Setup:

1. Install `pre-commit`.
2. Install `zizmor` so it is available on your `PATH`.
3. Run `pre-commit install` from the repository root.

Run manually:

- `pre-commit run zizmor --all-files`

## Reusable workflow: add issue to projects

Workflow location:

- `.github/workflows/add-issue-to-projects.yml`

What it does:

- Accepts an issue event and a list of project numbers.
- Constructs project URLs in the fixed `datasciencecampus` org.
- Adds the issue to each selected project.

Required organization credentials:

- `PROJECT_HANDLER_BOT_APP_ID` (Actions variable): GitHub App ID for the project handler bot.
- `PROJECT_HANDLER_BOT_PEM` (Actions secret): private key PEM for that GitHub App.
- Grant both to repositories that will call this workflow.

Example caller workflow in another repository:

```yaml
name: Add new issues to org projects

on:
  issues:
    types: [opened]

jobs:
  add-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@main
    with:
      project_numbers: |
        12
        194
```

Notes:

- `project_numbers` accepts comma-separated values or newline-separated values.
- Only numeric project numbers are supported.
- The project URL is built as `https://github.com/orgs/datasciencecampus/projects/<number>`.
- The workflow validates that each project number exists in the `datasciencecampus` org before attempting to add the issue.
- Calling workflows do not pass through secrets.
- The reusable workflow reads `PROJECT_HANDLER_BOT_APP_ID` directly from repository/organization variables.

## Reusable workflow: add pull request to projects and set field values

Workflow location:

- `.github/workflows/add-pr-to-projects.yml`

What it does:

- Runs from a caller workflow (for example on `pull_request` `opened`).
- Adds the opened pull request to one or more `datasciencecampus` Projects.
- Sets a field value for each configured project (for example `Status = In review`).

Caller workflow example:

```yaml
name: Add opened PR to projects

on:
  pull_request:
    types: [opened]

jobs:
  add-pr-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-pr-to-projects.yml@main
    with:
      project_field_values: |
        - project: 123
          field: Status
          value: In review
        - project: 194
          field: Status
          value: In review
```

Input format:

- `project_field_values` expects a list of mappings with keys: `project`, `field`, `value`.
- `project` should be the numeric project number in the `datasciencecampus` org.
- `pull_request_node_id` is optional and normally inferred from the pull request event payload.
