# GitHub Apps reference

This repository uses two GitHub Apps with distinct responsibilities and permission scopes.

## PROJECT_ROUTER_BOT

**Purpose:** Allows other repositories in the org to trigger workflows in this repository.

**Credentials (org-level, granted only to approved repositories):**

- `PROJECT_ROUTER_BOT_APP_ID`: Actions variable.
- `PROJECT_ROUTER_BOT_PEM`: Actions secret.

**Installation scope:** `datasciencecampus/github-actions` only.

**Permissions granted:**

- Actions: repository write.

The `actions: write` permission is the minimum required to call
`POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`
(the `workflow_dispatch` trigger endpoint). See
[ADR-0002](../explanation/ADR-0002-workflow-dispatch-over-repository-dispatch.md)
for why `workflow_dispatch` was chosen over `repository_dispatch`.

**Used in:** caller workflows in approved repositories (see how-to guides).

---

## PROJECT_HANDLER_BOT

**Purpose:** Manages ProjectsV2 boards on behalf of the org — adds items and sets field values.

**Credentials (stored in this repository's `project-automation` environment):**

- `PROJECT_HANDLER_BOT_APP_ID`: Actions variable.
- `PROJECT_HANDLER_BOT_PEM`: Actions secret.

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

**Used in:** `add-pr-to-projects.yml` and `add-issue-to-projects.yml` (internal to this repo — callers do not need these credentials).

## Central authorization variables

The `project-automation` environment in this repository must define the following variables:

- `PROJECT_ROUTER_ALLOWED_REPOSITORIES`: JSON array of repositories allowed to dispatch project-routing workflows, for example `[
"repo-a",
"repo-b"
]`.
- `PROJECT_ROUTER_ALLOWED_PROJECTS`: JSON object mapping repository name to approved project numbers, for example `{"repo-a":[194],"repo-b":[205,206]}`.

The workflows refuse to mint a project-handler token unless the requested repository is in the repository allowlist, every requested project number is approved for that repository, and the submitted issue or pull request node ID resolves back to that repository.
