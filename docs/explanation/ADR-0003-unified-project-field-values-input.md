# ADR-0003: Unified project_field_values input with optional field updates

- Status: Accepted
- Date: 2026-08-24

## Context

Two workflows add content to ProjectsV2 boards:

- `add-pr-to-projects` — always sets a field value (e.g. `Status = Review`) when adding
  a pull request.
- `add-issue-to-projects` — originally accepted only a list of project numbers
  (`project_numbers`), with no support for setting field values.

We needed to decide how the issue workflow should accept project configuration,
and whether a field update should be mandatory or optional.

## Decision

Both workflows accept a single `project_field_values` input: a JSON array of objects.
Each object must contain a `project` number. `field` and `value` are optional per entry
in the issue workflow — if omitted, the item is added to the project with no field update.

Example with no field update:

```json
[{"project": 194}]
```

Example with a field update:

```json
[{"project": 194, "field": "Status", "value": "Backlog"}]
```

## Rationale

1. **Consistent input format across workflows**
   Using the same `project_field_values` structure for both workflows reduces the
   cognitive overhead for callers who may use both. A single format is easier to
   document and reason about.

2. **Triage boards do not require field values**
   Many teams add issues to a backlog project with no initial field categorisation.
   Making `field`/`value` optional supports this common pattern without requiring a
   separate "add without fields" workflow.

3. **Replaces an inflexible predecessor format**
   The original `project_numbers` input (comma-separated integers) could not express
   field updates at all. `project_field_values` is strictly more expressive and
   backwards-compatible in spirit (a `{"project": N}` entry behaves identically to the
   old `N` in the project number list).

4. **Validation remains strict when fields are declared**
   If `field` is present, `value` is required and validated against the project's field
   options. Partial declarations (field without value) are rejected at runtime.

## Consequences

Positive:

- One input format to learn across both workflows.
- Issue workflow supports both simple triage (no fields) and structured routing
  (with fields) from the same entry point.
- Field validation catches misconfiguration before any mutations are made.

Negative:

- Callers migrating from `project_numbers` must update their dispatch payload format.
- `project_field_values` is a JSON string embedded in a workflow input, which requires
  careful escaping in shell contexts.

## Alternatives considered

1. Keep `project_numbers` for the issue workflow, add a separate `project_field_values`
   input for field updates
   Rejected because it creates two inputs with overlapping responsibility and no clear
   precedence when both are provided.

2. Make `field` and `value` required in the issue workflow (matching PR workflow behaviour)
   Rejected because it forces teams to configure a field even when they only want basic
   project membership, adding unnecessary friction for triage workflows.
