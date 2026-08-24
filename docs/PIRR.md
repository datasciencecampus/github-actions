# PIRR: Repository Visibility Decision

Private Internal Reasoning Record for this repository.

## Repo Name

github-actions

## Summary

This repository is intentionally internal visibility (not public by default), even though ONS GitHub usage policy generally prefers public repositories.

## Decision Record

- Decision date: 2026-08-24
- Next review date: 2027-02-24

## Why This Is an Exception

1. Security posture details
   This repository contains reusable security workflows and implementation details that describe internal scanning patterns, controls, and operational behavior. Publishing those details by default increases intelligence available to threat actors.

2. Organization-specific implementation
   Workflows and defaults are tightly aligned to internal standards, governance, and platform configuration. These details are useful internally but not broadly reusable without internal context.

3. Change-control and safe rollout
   Internal visibility allows controlled iteration while workflows mature, reducing the risk of external dependency on unstable interfaces.

4. Supply-chain risk management
   Keeping this repository internal by default reduces accidental exposure of internal workflow design decisions and integration assumptions.

## Alignment With Policy Intent

This exception supports the policy intent of responsible, secure, and maintainable software delivery.
When content is suitable for public sharing, it can be selectively published later with explicit review.

## Review Cadence

- Reassess visibility every 6 months (or sooner if needed).
- Reassess on major architecture or governance changes.

## Ownership

CODEOWNERS listed in `.github/CODEOWNERS` are responsible for this visibility decision, review cadence, and keeping this record current.
