# Contributing

Thanks for contributing.

## Workflow

1. Raise an issue first to describe the problem or enhancement.
2. Create a branch from `main` using GitHub's recommended format:
   - `<issue-number>-<issue-title-hyphenated>`
   - Example: `123-add-pr-project-status-workflow`
3. Keep changes tightly scoped to the issue.
4. Open a pull request when the change is ready.

## Repository selection

Before adding a new workflow here, consider whether it should be added to `ONSdigital/ons-github-actions` first.

Use this repository only when the workflow requires `datasciencecampus` organization-specific credentials or tokens and must remain within that org boundary.

## Security and secrets

- Never commit credentials, private keys, or tokens.
- Never print secrets in logs.
- Prefer organization secrets and variables already defined for reusable workflows.
- Keep permissions least-privilege in workflow definitions.

## Quality checks

Run checks before opening a PR:

- `pre-commit run --all-files`

Install the hooks locally, including the commit message hook:

- `pre-commit install --hook-type pre-commit --hook-type commit-msg`

Commit messages must follow the Conventional Commits format, for example:

- `feat: add project routing workflow`
- `fix: validate repository ownership before dispatch`
- `docs: clarify workflow prerequisites`

## Pull request guidance

- Link the issue in your PR description.
- Explain the user-visible behavior change.
- Include examples for workflow input/output changes.
- Keep unrelated refactors out of the same PR.
