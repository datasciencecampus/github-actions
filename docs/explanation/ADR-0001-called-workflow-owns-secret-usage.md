# ADR-0001: Called workflow owns secret usage

- Status: Accepted
- Date: 2026-08-24

## Context

This repository provides reusable GitHub Actions workflows for the datasciencecampus organization.

Some workflows require org-scoped credentials, including:

- PROJECT_HANDLER_BOT_APP_ID (organization variable)
- PROJECT_HANDLER_BOT_PEM (organization secret)

We needed to decide whether callers should pass secrets through to reusable workflows, or whether secret usage should be owned by the called workflow implementation.

## Decision

Use org-scoped credentials directly inside the called workflow implementation, and do not pass secrets through from callers.

In practice:

- Caller workflows provide functional inputs only.
- Reusable workflows read required org-level credentials internally.
- Caller workflows do not use secrets inherit for this workflow family.

## Rationale

1. Smaller attack surface at call sites
   Callers do not need to map or inherit secrets, which reduces accidental over-exposure in many repositories.

2. Centralized security controls
   Credential scope, rotation, and policy remain managed in one place (organization settings and called workflow code).

3. Clearer reusable workflow contract
   Inputs describe business intent (for example project mappings), not secret wiring.

4. Better policy alignment
   This avoids unconditional secret inheritance patterns that are commonly flagged by security tooling.

## Consequences

Positive:

- Simpler caller workflows.
- Fewer opportunities for misconfigured secret pass-through.
- Easier auditing of where sensitive credentials are consumed.

Negative:

- Reusable workflows depend on organization-level credential configuration.
- Consumers outside the datasciencecampus credential boundary cannot use these workflows as-is.

## Alternatives considered

1. Pass explicit secrets from callers
   Rejected because it increases repetitive configuration and secret handling risk across many repositories.

2. Use secrets inherit from callers
   Rejected because it is broader than needed and weakens least-privilege boundaries at the call site.
