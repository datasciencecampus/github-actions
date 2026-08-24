# ADR-0004: Separate reusable workflow pinning from dispatch ref

- Status: Accepted
- Date: 2026-08-24

## Context

This repository now exposes public reusable workflows for project routing:

- `add-issue-to-projects`
- `add-pr-to-projects`

These public workflows do not mutate ProjectsV2 directly. Instead, they mint a
router token and dispatch internal implementation workflows:

- `add-issue-to-projects-impl`
- `add-pr-to-projects-impl`

Some consumers in the organization must pin reusable workflows by commit SHA to
satisfy supply-chain policy.

However, the GitHub Actions `workflow_dispatch` API does not accept an arbitrary
commit SHA as the `ref` for a dispatch request. It requires a branch or tag name
that exists in the target repository. This means a caller can safely use:

- `uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@<commit-sha>`

but the public reusable workflow cannot simply pass that commit SHA through to
the internal `workflow_dispatch` call.

We therefore needed to decide how callers should pin the public reusable workflow
immutably while still giving the internal dispatch step a valid branch or tag ref.

## Decision

Separate the reusable workflow revision from the internal dispatch ref.

In practice:

- Callers may pin the public reusable workflow by commit SHA in `uses:`.
- Public reusable workflows accept an optional `implementation_ref` input.
- `implementation_ref` must be a branch or tag name that can be used with
  `workflow_dispatch`.
- If `implementation_ref` is omitted, the public reusable workflow derives the
  dispatch ref from `github.workflow_ref`.

Example caller:

```yaml
jobs:
  add-issue-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@<commit-sha>
    secrets:
      PROJECT_ROUTER_BOT_PRIVATE_KEY: ${{ secrets.PROJECT_ROUTER_BOT_PRIVATE_KEY }}
    with:
      implementation_ref: v1.0.1
      repository: ${{ github.event.repository.name }}
      issue_node_id: ${{ github.event.issue.node_id }}
      project_field_values: '[{"project":194}]'
```

## Rationale

1. **Supports mandatory SHA pinning at the call site**
   The reusable workflow itself can be pinned immutably with `@<commit-sha>`, which
   satisfies organizations that require SHA pinning for external workflow usage.

2. **Preserves compatibility with `workflow_dispatch` constraints**
   The internal implementation still runs through `workflow_dispatch`, which needs a
   branch or tag ref. `implementation_ref` makes that requirement explicit instead of
   hiding it behind brittle inference.

3. **Separates public contract from internal transport details**
   The caller states two distinct things: which reusable workflow revision to trust,
   and which implementation release line to dispatch. This is clearer than a single
   overloaded `ref` value that tries to mean both.

4. **Provides a sensible default for tag- and branch-pinned callers**
   Callers pinned to a tag or branch do not need extra configuration. The public
   reusable workflow can derive the same branch or tag from `github.workflow_ref`
   and dispatch the matching internal implementation.

5. **Works cleanly with release automation**
   Documentation and examples can auto-update `implementation_ref` through
   release-please without changing the caller's choice of SHA pinning strategy.

## Consequences

Positive:

- SHA-pinned consumers are supported without changing the internal dispatch model.
- The dispatch ref is explicit and audit-friendly when callers need SHA pinning.
- Branch- and tag-pinned consumers keep a simple default path.

Negative:

- Callers that pin by commit SHA must provide one additional input.
- Two versioning concepts now exist in caller configuration: workflow SHA and
  implementation branch/tag.
- Misconfigured `implementation_ref` values still fail at dispatch time if the
  named branch or tag does not exist.

## Alternatives considered

1. Infer a dispatch ref from the pinned commit SHA
   Rejected because a commit SHA is not a valid `workflow_dispatch` ref and cannot be
   reliably reverse-mapped to the intended release tag or branch.

2. Require all callers to pin by tag instead of commit SHA
   Rejected because some organization policies require immutable SHA pinning for
   third-party or cross-repository workflow usage.

3. Remove the internal `workflow_dispatch` hop and execute all logic directly in the
   public reusable workflow
   Rejected because the current split preserves the privileged implementation
   boundary and keeps router concerns separate from project-mutation concerns.

4. Keep a generic `ref` input on the public reusable workflow
   Rejected because it overloads two different meanings: reusable workflow revision
   and implementation dispatch target. `implementation_ref` is narrower and clearer.
