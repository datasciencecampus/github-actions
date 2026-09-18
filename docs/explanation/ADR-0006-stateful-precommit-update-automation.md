# ADR-0006: Stateful pre-commit update automation

- Status: Accepted
- Date: 2026-09-17

## Context

We needed to automate updates to the commit-pinned pre-commit hooks used by this repository without turning upstream release activity into an automatic dependency change to the default branch. The workflow must discover new SemVer tags, provide enough release context for review, remember update history, and create a pull request for a human to approve.

This introduces an architectural trust boundary: most workflow stages only inspect repository contents and public upstream metadata, while one final stage can write repository contents and create pull requests. It also introduces state because cooldown decisions cannot be made reliably from the current `.pre-commit-config.yaml` alone.

## Decision

Implement the automation as a stateful, staged workflow in `auto-update-precommit-hooks.yml`:

1. **Detect updates** from upstream SemVer tags and resolve each candidate tag to an immutable commit SHA. Only hooks with comparable SemVer tags are considered.
2. **Apply policy** using semver-level cooldowns measured from the first time this workflow observed the candidate tag/SHA pair, the configured skip list, and an explicit `force_update` override.
3. **Fetch release context** such as release notes and commit information for updates that passed policy.
4. **Write and propose changes** in a single job that updates `.pre-commit-config.yaml` and `configs/precommit-update-tracking.json`, pushes a bot branch, and creates a pull request. The default branch is changed only through the normal pull request review and merge process.

The workflow uses `contents: read` for filtering and release-context jobs. The detection job receives `contents: write` only to persist first-seen candidate metadata, and the final job receives `contents: write` and `pull-requests: write` to create the update branch and pull request. Actions use pinned commit SHAs, checkout does not persist credentials, and the GitHub token is passed only to the steps that need it.

When the workflow is called as a reusable workflow, each Python job checks out the caller repository into a `caller` workspace and checks out this repository into a separate `implementation` workspace at the invoked workflow SHA. The Python package is installed from `implementation`, while detection, tracking validation, configuration mutation, git commits, and pull request creation run from `caller`.

## Rationale

1. **Tag trust and reproducibility**
   SemVer tags are used as the human-readable update signal, but the configuration is updated to the resolved commit SHA. This preserves reviewable version information while preventing a mutable tag from changing the code consumed by pre-commit.

2. **Cooldowns reduce supply-chain exposure**
   A newly observed candidate tag is not adopted immediately by default. Major updates wait 28 days, minor updates 14 days, and patch updates 7 days from first observation. The graduated periods reflect increasing compatibility risk while allowing security and bug-fix updates to move sooner. The waiting period also provides time for upstream issues or malicious tags to become visible.

3. **Tracking state records adoption history**
   `configs/precommit-update-tracking.json` records the current SHA, current version, last update, last update time for each semver level, and first-seen timestamps for candidate tag/SHA pairs. Candidate metadata is committed when first observed so cooldown decisions remain stable across scheduled runs, while adoption history remains auditable in Git history.

4. **Pull requests preserve human control**
   The workflow creates a pull request containing release notes, commit information, cooldown policy, and risk warnings. It does not merge the change. Reviewers remain responsible for deciding whether an upstream release is suitable for the repository.

5. **Force updates remain explicit**
   `force_update` is available only as an explicit workflow input and is documented as a supply-chain risk. Keeping the normal path subject to cooldowns makes the secure behavior the default while preserving an operational escape hatch for urgent fixes.

6. **Write access is isolated**
   Separating read-only discovery from the write-enabled PR job limits the impact of failures or compromised data in upstream metadata. The write boundary is easy to audit and is reached only after the update has passed filtering and release-context collection.

## Consequences

Positive:

- Hook updates are commit-pinned, reviewable, and traceable to upstream SemVer tags.
- Scheduled runs make consistent cooldown decisions from tracked first-seen candidate timestamps.
- Dependency changes to the default branch are protected by the existing pull request review process.
- Read-only jobs do not need write-capable credentials.
- Release notes and risk information are available to reviewers in the generated pull request.

Negative:

- The tracking file is additional repository state that must remain consistent with `.pre-commit-config.yaml`.
- First-seen candidate metadata is committed directly so cooldown timers can advance before an update PR is eligible.
- Cooldowns delay adoption of some fixes and require an explicit override for urgent updates.
- The workflow is more complex than a direct `pre-commit autoupdate` job because it must resolve releases, preserve state, and construct a reviewable pull request.
- The generated pull request still requires human review and merge, so automation cannot guarantee that hooks are always current.

## Alternatives considered

1. **Update the default branch directly**
   - Pro: No pull request queue or manual merge step
   - Con: Removes the review gate for third-party code and would give scheduled automation direct write authority over the default branch

2. **Use mutable release tags in `.pre-commit-config.yaml`**
   - Pro: Simpler configuration and readable diffs
   - Con: A tag can be retargeted after review, so the consumed hook would not be reproducible

3. **Use only the current configuration as state**
   - Pro: No tracking file to maintain
   - Con: There is no durable record of when each semver level was last adopted, making adoption history less auditable

4. **Adopt every available release immediately**
   - Pro: Fastest access to upstream fixes
   - Con: Increases exposure to compromised or defective releases before they have had time to receive scrutiny

## Related decisions

- ADR-0001: Called workflow owns secret usage
- ADR-0002: Use workflow_dispatch instead of repository_dispatch
- ADR-0004: Separate reusable workflow pinning from dispatch ref