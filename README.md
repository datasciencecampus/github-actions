# github-actions

Reusable GitHub Actions workflows for the `datasciencecampus` GitHub organization.

This repository contains workflows that depend on `datasciencecampus` organization-scoped credentials and policies. For broadly reusable workflows that do not require this organization-specific boundary, use [ONSdigital/ons-github-actions](https://github.com/ONSdigital/ons-github-actions).

## Overview

This repository currently provides two public reusable workflows:

- `add-issue-to-projects`: add new issues to one or more `datasciencecampus` ProjectsV2 boards.
- `add-pr-to-projects`: add new pull requests to one or more `datasciencecampus` ProjectsV2 boards and set configured field values.

Each public reusable workflow has a matching internal implementation workflow. The public workflow is the caller-facing contract; the internal workflow owns the privileged `workflow_dispatch` path and project mutation logic.

## Workflow Catalog

### `add-issue-to-projects`

Adds opened issues to one or more `datasciencecampus` Projects by project number, with optional field updates.

- Public reusable workflow: [.github/workflows/add-issue-to-projects.yml](.github/workflows/add-issue-to-projects.yml)
- Internal implementation: [.github/workflows/add-issue-to-projects-impl.yml](.github/workflows/add-issue-to-projects-impl.yml)
- How-to guide: [docs/how-to/use-add-issue-to-projects-workflow.md](docs/how-to/use-add-issue-to-projects-workflow.md)
- Reusable workflow test: [.github/workflows/test-add-issue-to-projects-reusable.yml](.github/workflows/test-add-issue-to-projects-reusable.yml) (manual or `issues.opened`; requires repository variable `PROJECT_NUMBER` unless manual inputs are supplied)

### `add-pr-to-projects`

Adds opened pull requests to `datasciencecampus` Projects and sets configured field values, for example `Status = Review`.

- Public reusable workflow: [.github/workflows/add-pr-to-projects.yml](.github/workflows/add-pr-to-projects.yml)
- Internal implementation: [.github/workflows/add-pr-to-projects-impl.yml](.github/workflows/add-pr-to-projects-impl.yml)
- How-to guide: [docs/how-to/use-add-pr-to-projects-workflow.md](docs/how-to/use-add-pr-to-projects-workflow.md)
- Reusable workflow test: [.github/workflows/test-add-pr-to-projects-reusable.yml](.github/workflows/test-add-pr-to-projects-reusable.yml) (manual or `pull_request.opened`/`pull_request.reopened`; requires repository variable `PROJECT_NUMBER` unless manual inputs are supplied)

## Consumption Model

Consumers should call the public reusable workflows from other repositories using `uses:`.

- By default, the reusable workflows dispatch the release tag recorded in metadata stored alongside the invoked workflow revision.
- Set `implementation_ref` only when you need to override that release-managed dispatch target with a specific branch or tag.

> [!IMPORTANT]
> Public repositories that trigger these workflows automatically from issue or pull request creation events must restrict those events to trusted actors, for example by allowing only collaborators to open issues or pull requests. Configure this in the caller repository at `https://github.com/<owner>/<repo>/settings` under `Settings > General > Features`, then use `Issues > Issue permissions` or `Pull requests > Pull request permissions` as appropriate.

The full caller-facing contract, including required inputs and `implementation_ref` behavior, is documented in [docs/reference/reusable-workflows.md](docs/reference/reusable-workflows.md).

## Documentation

- Documentation index: [docs/README.md](docs/README.md)
- Workflow reference: [docs/reference/reusable-workflows.md](docs/reference/reusable-workflows.md)
- Architecture and ADRs: [docs/explanation/README.md](docs/explanation/README.md)
- Contribution guide: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)
