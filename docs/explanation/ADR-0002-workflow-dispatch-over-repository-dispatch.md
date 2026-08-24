# ADR-0002: Use workflow_dispatch instead of repository_dispatch

- Status: Accepted
- Date: 2026-08-24

## Context

Workflows in this repository need to be triggered from other repositories in the
`datasciencecampus` org. Two GitHub mechanisms exist for cross-repository workflow
triggering:

- `repository_dispatch` — sends a custom webhook event to a repository, requires a
  token with `contents: write` on the target repository.
- `workflow_dispatch` — triggers a specific named workflow via the Actions API,
  requires a token with `actions: write` on the target repository.

The dispatch GitHub App was provisioned with `actions: write` scoped to
`datasciencecampus/github-actions` so that other repositories could trigger workflows
here.

## Decision

Use `workflow_dispatch` (via `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`)
as the cross-repository trigger mechanism.

## Rationale

1. **Permission alignment**
   `workflow_dispatch` requires `actions: write`, which is the exact permission granted
   to the dispatch app. Using `repository_dispatch` instead would require
   `contents: write`, a broader permission that grants write access to repository
   content and is inconsistent with the app's intended scope.

2. **Explicit targeting**
   The endpoint names the specific workflow being invoked, making the dispatch intent
   unambiguous in both code and audit logs.

3. **Typed inputs**
   `workflow_dispatch` supports declared, typed inputs, giving the called workflow a
   validated contract rather than an opaque `client_payload` object.

4. **Least privilege**
   `actions: write` is narrower than `contents: write`. Keeping the dispatch app's
   permissions minimal limits the blast radius of a compromised token.

## Consequences

Positive:

- Dispatch token scope is as narrow as possible for the dispatch operation.
- Called workflow inputs are explicitly declared and validated by GitHub.
- Callers target a specific workflow file, preventing accidental cross-workflow event routing.

Negative:

- `workflow_dispatch` can only be triggered against a branch or tag that exists in the
  repository; callers must pass a valid `ref`. Callers running on pull request events
  must use `github.event.pull_request.head.ref` (not `github.ref_name`, which resolves
  to a synthetic merge ref).

## Alternatives considered

1. `repository_dispatch`
   Rejected because it requires `contents: write`, which is broader than necessary and
   conflicts with the `actions: write` scope already provisioned on the dispatch app.

2. Reusable workflows (`workflow_call`)
   Not applicable here because callers are in separate repositories and the credential
   boundary is managed centrally in `datasciencecampus/github-actions`.
