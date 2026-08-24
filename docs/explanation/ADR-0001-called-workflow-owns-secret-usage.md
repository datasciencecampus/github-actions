# ADR-0001: Called workflow owns secret usage

- Status: Accepted
- Date: 2026-08-24

## Context

This repository provides reusable GitHub Actions workflows for the datasciencecampus organization.

Some workflows require org-scoped dispatch credentials, including:

- PROJECT_ROUTER_BOT_APP_ID (organization variable)
- PROJECT_ROUTER_BOT_PRIVATE_KEY (organization secret)

We needed to decide whether callers should pass secrets through to reusable workflows, or whether sensitive project-mutation credential usage should be owned by the called workflow implementation.

## Decision

Keep project-mutation credentials inside the called workflow implementation, while allowing callers to provide only the narrower dispatch credential needed to trigger that implementation.

In practice:

- Caller workflows provide business inputs plus the dispatch private key required by the public reusable workflow.
- Internal implementation workflows read the project-mutation credentials inside this repository.
- Caller workflows do not use `secrets: inherit` for this workflow family.

## Rationale

1. Smaller attack surface at call sites
   Callers only provide the narrow dispatch secret instead of broader project-mutation credentials, which reduces accidental over-exposure in many repositories.

2. Centralized security controls
   Credential scope, rotation, and policy remain managed in one place (organization settings and called workflow code).

3. Clearer reusable workflow contract
   Most inputs describe business intent (for example project mappings), while secret wiring remains limited to the dispatch credential.

4. Better policy alignment
   This avoids unconditional secret inheritance patterns that are commonly flagged by security tooling.

## Consequences

Positive:

- Simpler caller workflows than passing multiple privileged credentials.
- Fewer opportunities for misconfigured secret pass-through of project-mutation credentials.
- Easier auditing of where sensitive credentials are consumed.

Negative:

- Reusable workflows depend on organization-level credential configuration.
- Consumers outside the datasciencecampus credential boundary cannot use these workflows as-is.

## Alternatives considered

1. Pass explicit project-mutation secrets from callers
   Rejected because it increases repetitive configuration and secret handling risk across many repositories.

2. Use secrets inherit from callers
   Rejected because it is broader than needed and weakens least-privilege boundaries at the call site.
