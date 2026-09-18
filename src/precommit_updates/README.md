# Pre-Commit Updates

`precommit_updates` contains the Python implementation used by the
`auto-update-precommit-hooks` GitHub Actions workflow.

The package keeps update policy and file mutation testable while leaving job
sequencing, permissions, and secrets in the workflow.

## CLI stages

Run the module from the repository root with `PYTHONPATH=src`:

```shell
PYTHONPATH=src python3 -m precommit_updates detect
PYTHONPATH=src python3 -m precommit_updates cooldown
PYTHONPATH=src python3 -m precommit_updates release-info
PYTHONPATH=src python3 -m precommit_updates apply
```

The stages correspond to the workflow jobs:

- `detect` finds newer SemVer tags, records first-seen candidate state, and resolves tags to commit SHAs.
- `cooldown` applies skip-list, force-update, and semver cooldown policy.
- `release-info` adds release notes and commits from the requested comparison range.
- `apply` updates the YAML and tracking files, creates one commit per hook, pushes
  the branch, and creates the pull request.

Each stage accepts optional paths:

```shell
PYTHONPATH=src python3 -m precommit_updates detect \
  --config .pre-commit-config.yaml \
  --tracking configs/precommit-update-tracking.json \
  --settings configs/precommit-updates-config.json
```

## Workflow contracts

The CLI reads and writes the following GitHub Actions environment values:

- `UPDATES_JSON` for the cooldown stage
- `ELIGIBLE_JSON` for the release-info stage
- `RELEASE_INFO` and `SKIPPED_UPDATES` for the apply stage
- `COOLDOWN_MAJOR`, `COOLDOWN_MINOR`, and `COOLDOWN_PATCH` as explicit overrides for `configs/precommit-updates-config.json`
- `FORCE_UPDATE` and `SKIP_HOOKS`, where `SKIP_HOOKS` overrides the persistent skip list when set

The `cooldown` and `apply` stages read `configs/precommit-updates-config.json`
by default. Missing keys fall back to built-in defaults, and invalid settings fail
the stage rather than silently ignoring the file.

When `GITHUB_OUTPUT` is set, stage output is written using the existing workflow
keys: `updates_found`, `updates_json`, `eligible_updates`, `skipped_updates`,
and `release_info`.

## Development

Install the runtime dependencies from the repository root and run the focused
unit tests:

```shell
pip install -r requirements.txt
python -m pytest tests/unit -q
```

The GitHub client is designed for mocked tests. Normal tests do not require
GitHub credentials or network access.
