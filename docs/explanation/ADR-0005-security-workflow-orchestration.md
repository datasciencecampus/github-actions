# ADR-0005: Security workflow orchestration pattern

- Status: Accepted
- Date: 2026-09-07

## Context

We needed to provide GitHub Actions security scanning (zizmor) and infrastructure-as-code scanning (checkov) to the datasciencecampus organization. Both are independent tools that analyze different aspects of repositories.

The decision was whether to:

1. Create two independent workflows that trigger separately on each event
2. Create an orchestrator workflow that calls both tools in parallel

## Decision

Create a single orchestrator workflow (`security-analysis.yml`) that runs on `push` and `pull_request` events and calls two child workflows (`zizmor.yml` and `checkov.yml`) in parallel.

- `security-analysis.yml`: Public-facing orchestrator with triggers and concurrency management
- `zizmor.yml`: Reusable-only child workflow (workflow_call only)
- `checkov.yml`: Reusable-only child workflow (workflow_call only)

## Rationale

1. **Unified concurrency management**
   Both tools run/cancel as a single unit. This prevents duplicate runs or partial executions where one tool completes while the other is canceled.

2. **Single source of truth for triggers**
   All event configuration (push to main, pull_request against main) lives in one place. Adding new triggers only requires updating the orchestrator.

3. **Consistent SARIF uploads**
   Both tools' results are subject to the same advanced-security policy (auto-enable for public repos, auto-disable for private repos by default).

4. **Flexible customization**
   - Organization default behavior via `security-analysis.yml` on push/PR
   - Caller customization via workflow_call inputs (config paths, persona, advanced-security override)

5. **Clear caller contract**
   Repositories should call `security-analysis.yml`, not individual tool workflows. This prevents confusion about which workflow to use and runs both tools together through the supported entry point.

6. **Parallel execution**
   Both tools run in parallel, reducing overall workflow runtime compared to sequential execution.

## Consequences

Positive:

- Simpler mental model for repository maintainers (one workflow to add, not two)
- Consistent results when callers use the orchestrator: both tools run together
- Easier to update default behavior organization-wide (one place to change)
- Provides one recommended entry point that includes both tools
- Flexible customization for specific repositories via workflow_call

Negative:

- If one tool needs to run independently, we'd need to refactor the architecture
- Child workflows expose `workflow_call` and can be called directly, but direct calls bypass the orchestrator's shared triggers, concurrency, and combined-results contract
- Orchestrator adds one layer of indirection (minimal performance impact)

## Alternatives considered

1. **Two independent workflows**
   - Pro: Maximum flexibility
   - Con: Duplicate trigger logic, possible race conditions with concurrency, inconsistent SARIF upload policies

2. **Composite action wrapper**
   - Pro: Could wrap both tools
   - Con: Composite actions don't support workflow triggers or SARIF uploads

3. **Orchestrator + direct child calls**
   - Current decision; child workflows expose only `workflow_call`. Callers should use the orchestrator to run both tools together, although GitHub does not prevent direct calls to an individual child workflow.

## Related decisions

- ADR-0001: Called workflow owns secret usage (applies to child workflows here)
- ADR-0004: Separate reusable pinning from dispatch ref (applies to orchestrator caller patterns)
