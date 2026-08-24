# github-actions

Reusable workflows for the Data Science Campus GitHub organization.

This repository is the sister repository to [ONSdigital/ons-github-actions](https://github.com/ONSdigital/ons-github-actions).

- Use [ONSdigital/ons-github-actions](https://github.com/ONSdigital/ons-github-actions) for broadly reusable workflows.
- Use this repository for workflows that require `datasciencecampus` org-scoped credentials.

## Start here

- Documentation index: [docs/README.md](docs/README.md)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)

## Reusable workflows

### add-issue-to-projects

Adds opened issues to one or more `datasciencecampus` Projects by project number.

- Public reusable workflow: [.github/workflows/add-issue-to-projects.yml](.github/workflows/add-issue-to-projects.yml)
- Internal implementation: [.github/workflows/add-issue-to-projects-impl.yml](.github/workflows/add-issue-to-projects-impl.yml)
- How-to: [docs/how-to/use-add-issue-to-projects-workflow.md](docs/how-to/use-add-issue-to-projects-workflow.md)
- Test workflow: [.github/workflows/test-add-issue-to-projects-reusable.yml](.github/workflows/test-add-issue-to-projects-reusable.yml)

### add-pr-to-projects

Adds opened pull requests to `datasciencecampus` Projects and sets configured field values (for example `Status = Review`).

- Public reusable workflow: [.github/workflows/add-pr-to-projects.yml](.github/workflows/add-pr-to-projects.yml)
- Internal implementation: [.github/workflows/add-pr-to-projects-impl.yml](.github/workflows/add-pr-to-projects-impl.yml)
- How-to: [docs/how-to/use-add-pr-to-projects-workflow.md](docs/how-to/use-add-pr-to-projects-workflow.md)
- Test workflow: [.github/workflows/test-add-pr-to-projects-reusable.yml](.github/workflows/test-add-pr-to-projects-reusable.yml)

### Shared reference

- Reusable workflows contract and inputs: [docs/reference/reusable-workflows.md](docs/reference/reusable-workflows.md)

## Rationale

- Explanation docs: [docs/explanation/README.md](docs/explanation/README.md)
