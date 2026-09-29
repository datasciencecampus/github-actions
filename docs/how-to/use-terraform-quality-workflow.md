# Use terraform-quality

Run Terraform formatting checks, validation, and TFLint analysis with the reusable workflow.

Reusable workflow: `.github/workflows/terraform-quality.yml`

## Prerequisites

- Terraform configuration must be under the caller repository's `terraform/` directory.
- When TFLint is enabled, the caller repository must include `configs/.tflint.hcl`.
- No secrets are required. The workflow needs `contents: read` to check out and validate the caller's repository.

## Add to your repository

Create `.github/workflows/terraform-quality.yml` in your repository:

```yaml
name: Terraform Quality

on:
  push:
  pull_request:
    branches: ["main"]

run-name: "${{ github.workflow }} - ${{ github.actor }} - ${{ github.event_name == 'pull_request' && format('PR #{0}', github.event.pull_request.number) || github.ref_name }}"

permissions: {} # Deny token access by default; jobs grant only what they need.

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  terraform-quality:
    name: terraform-quality
    uses: datasciencecampus/github-actions/.github/workflows/terraform-quality.yml@caf4ab7c789a34efb07d61113830bcb67d634a38 # v1.7.0
    permissions:
      contents: read # Required to check out and validate Terraform configuration.
    with:
      terraform-dirs: '["terraform/01_sandbox", "terraform/02_dev_nonprod", "terraform/03_stg_prod", "terraform/04_prd_prod", "terraform/modules"]'
      terraform-version: "1.16.4" # This should match the terraform version used in the repo.
      run-fmt: true
      run-validate: true
      run-tflint: true
```

The top-level `permissions: {}` denies token access by default. The reusable-workflow job grants only `contents: read`; Terraform quality checks do not need the `security-events: write` or `actions: read` permissions used by the security-analysis workflow.

## Inputs and check scope

- `terraform-dirs`: JSON array of repository-relative Terraform directories to validate. The workflow validates the JSON and rejects empty, absolute, or traversal paths. By default, it validates the four standard environment directories.
- `terraform-version`: Terraform version to install. The workflow default is `1.14.3`; the example pins `1.16.4` explicitly.
- `run-fmt`, `run-validate`, and `run-tflint`: Enable or skip each check. All default to `true`.
- `continue_on_error`: Optional test input, default `false`. When enabled, validation check failures do not fail the workflow; input validation errors still prevent the checks from running.

`terraform-dirs` selects directories for `terraform validate`. The format check and TFLint currently scan the `terraform/` directory recursively, regardless of this input.

## Results

Each check runs as a separate job in the Actions workflow. A failed enabled check fails the caller's workflow run; disabled checks are skipped.