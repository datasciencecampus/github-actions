# Copilot Instructions

This repository contains reusable GitHub Actions workflows for the `datasciencecampus` GitHub organization.

## Repository purpose

- Use this repository when a workflow needs `datasciencecampus` credentials or policies, or when public repositories must be able to call it.
- Use `ONSdigital/ons-github-actions` for broadly reusable workflows only if every caller can access that internal repository. Public repositories cannot call it.

## Security posture

- Changes in this repository should follow secure-by-design principles.
- Prefer designs that reduce attack surface by default rather than relying on callers to configure safety correctly.
- Align workflow changes with UK government good practice for secure services: least privilege, explicit trust boundaries, validated inputs, safe defaults, clear auditability, and minimal secret exposure.
- When there is a tradeoff between convenience and stronger default security, prefer the more secure default unless the user explicitly asks for another approach.

## Workflow structure

- Project-routing public caller-facing workflows use the clean `add-*` names:
  - `.github/workflows/add-issue-to-projects.yml`
  - `.github/workflows/add-pr-to-projects.yml`
- Other public reusable workflow entry points are:
  - `.github/workflows/security-analysis.yml` (orchestrates zizmor and Checkov)
  - `.github/workflows/terraform-quality.yml`
- Security-analysis child workflows are `.github/workflows/zizmor.yml` and `.github/workflows/checkov.yml`; callers should use the orchestrator so both tools share its trigger and policy configuration.
- Internal project-routing implementations use `*-impl` names:
  - `.github/workflows/add-issue-to-projects-impl.yml`
  - `.github/workflows/add-pr-to-projects-impl.yml`
- Reusable workflow tests use `test-*-reusable` names:
  - `.github/workflows/test-add-issue-to-projects-reusable.yml`
  - `.github/workflows/test-add-pr-to-projects-reusable.yml`
  - `.github/workflows/test-terraform-quality-reusable.yml`

Do not collapse the project-routing public and internal workflows back into one file unless the user explicitly asks for that architectural change.

## Public contract conventions

- The public `add-*` workflows are the caller API for project routing. The internal `*-impl` workflows are dispatch-only and should not be documented as the caller entrypoint.
- `security-analysis.yml` and `terraform-quality.yml` are public `workflow_call` entry points. Their inputs and permission requirements belong in the reusable-workflow reference and their relevant how-to guides.
- If a caller-facing contract changes, update the relevant items together:
  - `README.md`
  - `docs/reference/reusable-workflows.md`
  - relevant `docs/how-to/*.md`
  - `docs/how-to/README.md` or `docs/README.md` when pages or navigation change
- If the change is architectural rather than cosmetic, add or update an ADR under `docs/explanation/adr/` and link it from `docs/explanation/adr/README.md`.

## Pinning and dispatch gotchas

- These dispatch and `implementation_ref` rules apply to the project-routing workflows, not to security-analysis or terraform-quality.
- `workflow_dispatch` requires a branch or tag ref, not a raw commit SHA.
- Project-routing public reusable workflows support SHA pinning at the `uses:` boundary, but their internal dispatch still needs a branch or tag ref.
- If `implementation_ref` is omitted, the project-routing workflow first uses `github.workflow_ref` when that is already a branch or tag.
- For SHA-pinned project-routing callers, the public workflow reads `configs/implementation-ref.json` from the pinned workflow revision, takes `implementation_version`, and dispatches the matching `v...` tag.
- For project-routing pull request contexts, do not dispatch on `refs/pull/*/merge`; use the PR head branch.

## Secrets and credentials

- Caller-side router credentials are used only by project-routing workflows:
  - `PROJECT_ROUTER_BOT_APP_ID`
  - `PROJECT_ROUTER_BOT_PRIVATE_KEY`
- Internal implementation credentials are used only by project-routing implementations:
  - `PROJECT_HANDLER_BOT_APP_ID`
  - `PROJECT_HANDLER_BOT_PRIVATE_KEY`
- Do not use `secrets: inherit` for this workflow family unless the user explicitly requests it.
- Prefer explicit secret mappings and least-privilege permissions.
- Keep credential use inside the narrowest possible workflow boundary.
- Do not broaden GitHub token or app permissions without a clear repository-specific reason.
- Validate repository ownership, organization scope, and object provenance before mutating projects or dispatching privileged workflows.
- Security-analysis callers should grant only `actions: read`, `contents: read`, and `security-events: write` to the reusable-workflow job. Terraform-quality callers need only `contents: read`. Prefer `permissions: {}` at workflow level and explicit job-level grants.

## Release Please conventions

- Release automation is managed by `.github/workflows/release-please.yml` and `release-please-config.json`.
- `configs/implementation-ref.json` stores the release-managed `implementation_version` used for project-routing SHA-pinned dispatch resolution.
- Release Please updates `configs/implementation-ref.json` via the JSON updater; workflows prepend `v` when dispatching.
- Internal test workflows use local reusable workflow paths and should not be version-pinned or wired into release-please version bumping.

## Documentation conventions

- Keep docs concise and task-oriented.
- Use `docs/how-to/` for usage steps, `docs/reference/` for exact contracts, and `docs/explanation/` for rationale.
- Use the category index pages in `docs/README.md` to navigate to lower-level indexes. Put ADRs in `docs/explanation/adr/` and maintain that folder's `README.md` index.
- When examples show consumer workflows, prefer `@<commit-sha>` without `implementation_ref` unless the example is explicitly showing an override.

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