# ADR-0003: Structured Output Contract = TradePlan.v1

- Status: Accepted
- Date: 2026-03-05
- Owners: TradingAgents Fork Maintainers
- Related PR: PR-4

## Context
The existing runtime emits a final free-form decision string and then extracts `BUY/SELL/HOLD`.
This is useful for compatibility but insufficient for downstream automation that needs typed fields.
We need a stable structured contract without breaking existing behavior.

## Decision
Adopt `TradePlan.v1` as the structured output contract and emit it on every run.
The runtime keeps existing decision extraction unchanged and adds `trade_plan` as an additional output field.

`TradePlan.v1` includes:
- `schema_version`
- `symbol`
- `date`
- `action`
- `position_size`
- `constraints`
- `confidence`
- `rationale`
- `evidence_refs`

Generation uses the quick LLM with strict JSON prompting and a bounded JSON repair loop.
If parsing/validation still fails, emit a safe fallback HOLD plan.

## Alternatives Considered
- Keep only free-form text output:
  - Pros: no implementation work
  - Cons: weak machine-readability and fragile integrations
- Introduce optional schema only in CLI layer:
  - Pros: lower impact
  - Cons: not guaranteed across non-CLI entry points

## Consequences
- Positive:
  - Deterministic contract for automation and logging
  - Backwards compatibility preserved
  - Explicit failure-safe behavior
- Negative:
  - Additional LLM call for structured output generation
  - Small complexity increase in output pipeline
- Risks/Mitigations:
  - Risk: malformed JSON outputs
  - Mitigation: validation + repair retries + safe HOLD fallback

## Rollout Plan
1. Add schema contract and validator.
2. Add builder with strict JSON prompt and repair loop.
3. Integrate into graph propagate/log output.
4. Document contract and failure rules.

## Validation
- `python -m compileall .`
- Manual sample runs should confirm:
  - existing decision string still returned
  - `trade_plan` is present in logged final state JSON
