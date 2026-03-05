# ADR Policy

## Rule
Any architectural change must include an ADR file with a unique ID.

## Location
- Store ADRs in `docs/ADR/`.
- File naming convention:
  - `ADR-0001-short-title.md`
  - `ADR-0002-another-title.md`

## When ADR Is Required
Create/update an ADR when changing:
- Runtime architecture boundaries.
- Configuration model or loading strategy.
- Output schema contracts.
- Persistence/logging contracts.
- External provider integration shape.

## ADR Template
Use this template for every new ADR:

```md
# ADR-XXXX: <Title>

- Status: Proposed | Accepted | Superseded
- Date: YYYY-MM-DD
- Owners: <team/person>
- Related PR: <link or id>

## Context
Describe the problem and constraints.

## Decision
State the chosen approach clearly.

## Alternatives Considered
- Option A: <pros/cons>
- Option B: <pros/cons>

## Consequences
- Positive:
- Negative:
- Risks/Mitigations:

## Rollout Plan
Implementation and migration steps.

## Validation
How the decision is tested or verified.
```
