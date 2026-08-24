# ADR-0004: Separate reusable workflow pinning from dispatch ref

- Status: Accepted
- Date: 2026-08-24

## Context

This repository now exposes public reusable workflows for project routing:

- `add-issue-to-projects`
- `add-pr-to-projects`

These public workflows do not mutate ProjectsV2 directly. Instead, they mint a
dispatch token and dispatch internal implementation workflows:

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
- Public reusable workflows accept an optional `implementation_ref` override.
- If `implementation_ref` is omitted, the public reusable workflow derives the
   dispatch ref from a release-managed metadata file in the invoked workflow revision.
- It turns the stored release version into the matching `v...` dispatch tag.

Example caller:

```yaml
jobs:
  add-issue-to-projects:
    uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@<commit-sha>
    secrets:
      PROJECT_ROUTER_BOT_PRIVATE_KEY: ${{ secrets.PROJECT_ROUTER_BOT_PRIVATE_KEY }}
    with:
      repository: ${{ github.event.repository.name }}
      issue_node_id: ${{ github.event.issue.node_id }}
         project_field_values: '[{"project":1234}]'
```

## Rationale

1. **Supports mandatory SHA pinning at the call site**
   The reusable workflow itself can be pinned immutably with `@<commit-sha>`, which
   satisfies organizations that require SHA pinning for external workflow usage.

2. **Preserves compatibility with `workflow_dispatch` constraints**
   The internal implementation still runs through `workflow_dispatch`, which needs a
   branch or tag ref. The pinned workflow revision carries the intended release
   version as explicit metadata, and callers can still override it explicitly when
   needed.

3. **Keeps a simple default for SHA-pinned callers**
   Most callers no longer need to carry a second version field. The pinned
   workflow revision carries the release-managed version that becomes the
   dispatch tag.

4. **Provides a single predictable default for callers**
   Callers do not need extra configuration when the release-managed metadata is
   correct. The public reusable workflow uses that metadata to resolve the
   implementation dispatch tag.

## Consequences

Positive:

- SHA-pinned consumers usually do not need a second version input.
- The dispatched tag is explicit and audit-friendly for the pinned workflow revision.
- Branch-, tag-, and SHA-pinned consumers keep the same default path.

Negative:

- The dispatch ref metadata must be kept correct as part of the release process.
- Two versioning concepts can still exist in caller configuration when a caller
   chooses to override the dispatch target explicitly.
- Misconfigured `implementation_ref` values still fail at dispatch time if the
  named branch or tag does not exist.

## Alternatives considered

1. Infer a dispatch ref from the pinned commit SHA
   Rejected because a commit SHA is not a valid `workflow_dispatch` ref and cannot be
   reliably reverse-mapped to the intended release tag or branch.

2. Store the dispatch ref as release-managed metadata in the workflow repository
   Accepted because it keeps the dispatch ref aligned with the pinned workflow
   revision and avoids Dependabot drift.

3. Require all callers to pin by tag instead of commit SHA
   Rejected because some organization policies require immutable SHA pinning for
   third-party or cross-repository workflow usage.

4. Remove the internal `workflow_dispatch` hop and execute all logic directly in the
   public reusable workflow
   Rejected because the current split preserves the privileged implementation
   boundary and keeps dispatch concerns separate from project-mutation concerns.

5. Keep a generic `ref` input on the public reusable workflow
   Rejected because it overloads two different meanings: reusable workflow revision
   and implementation dispatch target. `implementation_ref` is narrower and clearer.
