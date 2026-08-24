# GitHub Apps reference

This repository uses two GitHub Apps with distinct responsibilities and permission scopes.

## Dispatch credentials

**Purpose:** Allows approved caller repositories to trigger workflows in this repository.

- `PROJECT_ROUTER_BOT_APP_ID`: Actions variable.
- `PROJECT_ROUTER_BOT_PRIVATE_KEY`: Actions secret.

**Installation scope:** `datasciencecampus/github-actions` only.

**Permissions granted:**

- Actions: repository write.

The `actions: write` permission is the minimum required to call
`POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`
(the `workflow_dispatch` trigger endpoint). See
[ADR-0002](../explanation/ADR-0002-workflow-dispatch-over-repository-dispatch.md)
for why `workflow_dispatch` was chosen over `repository_dispatch`.

**Used in:** caller workflows in approved repositories that are provisioned for this integration (see how-to guides).

---

## Project automation credentials

**Purpose:** Manages ProjectsV2 boards on behalf of the org — adds items and sets field values.

- `PROJECT_HANDLER_BOT_APP_ID`: Actions variable.
- `PROJECT_HANDLER_BOT_PRIVATE_KEY`: Actions secret.

**Installation scope:** `datasciencecampus` organisation.

**Permissions granted:**

- Organization projects: organization write.
- Pull requests: repository read.
- Issues: repository read.

- `organization-projects: write` is required to call `addProjectV2ItemById` and
  `updateProjectV2ItemFieldValue` via the GitHub GraphQL API.
- `pull-requests: read` is required for the GraphQL API to resolve a pull request node
  ID when adding it to a project.
- `issues: read` is required for the GraphQL API to resolve an issue node ID when
  adding it to a project.

**Used in:** `add-pr-to-projects-impl.yml` and `add-issue-to-projects-impl.yml` (internal to this repo — callers do not need these credentials).

The workflows only mint a project automation token for repositories within the `datasciencecampus` organisation, and they verify that the submitted issue or pull request node ID resolves back to the repository named in the request.
