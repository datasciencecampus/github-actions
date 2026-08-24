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
- Reusable workflow test: [.github/workflows/test-add-issue-to-projects-reusable.yml](.github/workflows/test-add-issue-to-projects-reusable.yml)

### `add-pr-to-projects`

Adds opened pull requests to `datasciencecampus` Projects and sets configured field values, for example `Status = Review`.

- Public reusable workflow: [.github/workflows/add-pr-to-projects.yml](.github/workflows/add-pr-to-projects.yml)
- Internal implementation: [.github/workflows/add-pr-to-projects-impl.yml](.github/workflows/add-pr-to-projects-impl.yml)
- How-to guide: [docs/how-to/use-add-pr-to-projects-workflow.md](docs/how-to/use-add-pr-to-projects-workflow.md)
- Reusable workflow test: [.github/workflows/test-add-pr-to-projects-reusable.yml](.github/workflows/test-add-pr-to-projects-reusable.yml)

## Consumption Model

Consumers should call the public reusable workflows from other repositories using `uses:`.

- By default, the reusable workflows dispatch the release tag recorded in metadata stored alongside the invoked workflow revision.
- Set `implementation_ref` only when you need to override that release-managed dispatch target with a specific branch or tag.

The full caller-facing contract, including required inputs and `implementation_ref` behavior, is documented in [docs/reference/reusable-workflows.md](docs/reference/reusable-workflows.md).

## Documentation

- Documentation index: [docs/README.md](docs/README.md)
- Workflow reference: [docs/reference/reusable-workflows.md](docs/reference/reusable-workflows.md)
- Architecture and ADRs: [docs/explanation/README.md](docs/explanation/README.md)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
