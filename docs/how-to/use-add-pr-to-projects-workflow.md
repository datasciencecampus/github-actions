# Use add-pr-to-projects via repository_dispatch

Use this workflow when a pull request is opened and you want to add it to one or more `datasciencecampus` Projects, then set a field value (for example `Status = Review`).

Workflow:

- `.github/workflows/add-pr-to-projects.yml` in this repository

## Prerequisites

1. The caller can send `repository_dispatch` to `datasciencecampus/github-actions`.
2. Organization credentials are available to this workflow:

- `PROJECT_HANDLER_BOT_APP_ID` (variable)
- `PROJECT_HANDLER_BOT_PEM` (secret)

3. Each target project and field exists in `datasciencecampus` Projects.

## Trigger this repo via repository_dispatch

If you want execution to happen in `datasciencecampus/github-actions` (for example to use its environment secrets), trigger this workflow with a repository dispatch event.

Example using GitHub CLI:

```bash
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/datasciencecampus/github-actions/dispatches \
  -f event_type='add-pr-to-projects' \
  -f client_payload='{
    "repository":"my-caller-repo",
    "pull_request_node_id":"PR_kwDOExample",
    "project_field_values":"[{\"project\":194,\"field\":\"Status\",\"value\":\"Review\"}]"
  }'
```

Create a workflow in your repository to send the dispatch event:

```yaml
name: Dispatch add-pr-to-projects

on:
  pull_request:
    types: [opened]

permissions:
  contents: read

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Send repository_dispatch
        env:
          DISPATCH_TOKEN: ${{ secrets.GH_ACTIONS_DISPATCH_TOKEN }}
        run: |
          curl -sS -L \
            -X POST \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${DISPATCH_TOKEN}" \
            https://api.github.com/repos/datasciencecampus/github-actions/dispatches \
            -d @- <<'JSON'
          {
            "event_type": "add-pr-to-projects",
            "client_payload": {
              "repository": "${{ github.event.repository.name }}",
              "pull_request_node_id": "${{ github.event.pull_request.node_id }}",
              "project_field_values": "[{\"project\":194,\"field\":\"Status\",\"value\":\"Review\"}]"
            }
          }
          JSON
```

## Mapping input

Pass a list of dictionaries in `project_field_values`.

Each entry should include:

- `project`: numeric project number
- `field`: project field name
- `value`: value to set for that field

Example entry:

- `{"project": 194, "field": "Status", "value": "Review"}`

Dispatch payload fields:

- `project_field_values` (required): JSON string list of mappings
- `pull_request_node_id` (required): pull request node id
- `repository` (optional): source repository name for token scoping
