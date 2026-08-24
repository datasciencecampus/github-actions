# Copilot Instructions

This repository contains reusable GitHub Actions workflows for the `datasciencecampus` GitHub organization.

## Repository purpose

- Use this repository only for workflows that require `datasciencecampus` organization-scoped credentials or policies.
- Prefer `ONSdigital/ons-github-actions` for broadly reusable workflows that do not depend on this org boundary.

## Security posture

- Changes in this repository should follow secure-by-design principles.
- Prefer designs that reduce attack surface by default rather than relying on callers to configure safety correctly.
- Align workflow changes with UK government good practice for secure services: least privilege, explicit trust boundaries, validated inputs, safe defaults, clear auditability, and minimal secret exposure.
- When there is a tradeoff between convenience and stronger default security, prefer the more secure default unless the user explicitly asks for another approach.

## Workflow structure

- Public caller-facing workflows use the clean `add-*` names:
  - `.github/workflows/add-issue-to-projects.yml`
  - `.github/workflows/add-pr-to-projects.yml`
- Internal privileged implementations use `*-impl` names:
  - `.github/workflows/add-issue-to-projects-impl.yml`
  - `.github/workflows/add-pr-to-projects-impl.yml`
- Reusable workflow tests use `*-reusable` names:
  - `.github/workflows/test-add-issue-to-projects-reusable.yml`
  - `.github/workflows/test-add-pr-to-projects-reusable.yml`

Do not collapse the public and internal workflows back into one file unless the user explicitly asks for that architectural change.

## Public contract conventions

- The public `add-*` workflows are the API that other repositories consume via `uses:`.
- The internal `*-impl` workflows are dispatch-only and should not be documented as the primary caller entrypoint.
- If caller-facing inputs change, update all of these together:
  - `README.md`
  - `docs/reference/reusable-workflows.md`
  - relevant `docs/how-to/*.md`
- If the change is architectural rather than cosmetic, add or update an ADR under `docs/explanation/`.

## Pinning and dispatch gotchas

- `workflow_dispatch` requires a branch or tag ref, not a raw commit SHA.
- Public reusable workflows support SHA pinning at the `uses:` boundary, but internal dispatch uses the optional `implementation_ref` input when callers need explicit branch/tag control.
- If `implementation_ref` is omitted, the public reusable workflow derives a dispatchable ref from `github.workflow_ref`.
- For pull request contexts, do not dispatch on `refs/pull/*/merge`; use the PR head branch.

## Secrets and credentials

- Caller-side router credentials:
  - `PROJECT_ROUTER_BOT_APP_ID`
  - `PROJECT_ROUTER_BOT_PRIVATE_KEY`
- Internal implementation credentials:
  - `PROJECT_HANDLER_BOT_APP_ID`
  - `PROJECT_HANDLER_BOT_PRIVATE_KEY`
- Do not use `secrets: inherit` for this workflow family unless the user explicitly requests it.
- Prefer explicit secret mappings and least-privilege permissions.
- Keep credential use inside the narrowest possible workflow boundary.
- Do not broaden GitHub token or app permissions without a clear repository-specific reason.
- Validate repository ownership, organization scope, and object provenance before mutating projects or dispatching privileged workflows.

## Release Please conventions

- Release automation is managed by `.github/workflows/release-please.yml` and `release-please-config.json`.
- The how-to guides contain `implementation_ref` example lines annotated with `x-release-please-version` so release-please can update them automatically.
- Do not remove or rewrite those annotations casually.
- Internal test workflows use local reusable workflow paths and should not be version-pinned or wired into release-please version bumping.

## Documentation conventions

- Keep docs concise and task-oriented.
- Use `docs/how-to/` for usage steps, `docs/reference/` for exact contracts, and `docs/explanation/` for rationale.
- When examples show consumer workflows, prefer `@<commit-sha>` plus `implementation_ref: v...` in line with the current SHA-pinning design.

## Change discipline

- Keep workflow changes tightly scoped.
- Prefer small, incremental changes over broad rewrites.
- Preserve existing behavior unless the user explicitly requests a contract change.
- Preserve repository-ownership and organization-validation checks.
- Preserve least-privilege token permissions unless a change clearly requires widening them.
- Prefer fail-safe behavior: reject unclear, malformed, or over-broad inputs rather than guessing.
- Avoid adding convenience shortcuts that weaken the current trust boundary between public reusable workflows and internal implementations.
- Treat auditability as a requirement: workflow names, inputs, permissions, and dispatch targets should remain explicit and easy to reason about.
- When changing workflow inputs or dispatch behavior, validate the edited YAML files and check the adjacent docs in the same change.
- Aim for production-ready outcomes: complete the caller contract, validation, and documentation updates needed for the change to be safely used.

## Commit and PR conventions

- Follow Conventional Commits.
- Use a breaking change marker (`!` and/or `BREAKING CHANGE:` footer) when renaming public workflow entrypoints or otherwise changing caller-facing contracts.
- Keep unrelated refactors out of the same PR.