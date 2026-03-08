# SSOT Index (One Item, One File)

Canonical SSOT records are split by type, and each item has its own YAML file.

## FR (Functional Requirements)
- `docs/ssot/fr/FR-001-yaml-config-loading.yaml`
- `docs/ssot/fr/FR-002-local-llm-runtime-profile.yaml`
- `docs/ssot/fr/FR-003-tradeplan-v1-output.yaml`
- `docs/ssot/fr/FR-004-experiment-runner.yaml`
- `docs/ssot/fr/FR-005-graph-orchestration-workflow.yaml`
- `docs/ssot/fr/FR-006-llm-provider-routing.yaml`
- `docs/ssot/fr/FR-007-data-vendor-routing.yaml`
- `docs/ssot/fr/FR-008-cli-analysis-session.yaml`

## NFR (Non-Functional Requirements)
- `docs/ssot/nfr/NFR-001-config-reproducibility.yaml`
- `docs/ssot/nfr/NFR-002-tradeplan-parse-error-handling.yaml`
- `docs/ssot/nfr/NFR-003-log-contract-stability.yaml`
- `docs/ssot/nfr/NFR-004-experiment-metrics-consistency.yaml`
- `docs/ssot/nfr/NFR-005-bounded-execution-controls.yaml`
- `docs/ssot/nfr/NFR-006-data-artifact-path-stability.yaml`
- `docs/ssot/nfr/NFR-007-provider-compatibility-constraints.yaml`
- `docs/ssot/nfr/NFR-008-cli-session-observability.yaml`

## ADR (Architecture Decision Records)
- `docs/ssot/adr/ADR-0002-local-llm-standard-openai-compatible.yaml`
- `docs/ssot/adr/ADR-0003-structured-output-tradeplan-v1.yaml`
- `docs/ssot/adr/ADR-0004-ssot-split-fr-nfr-adr.yaml`
- `docs/ssot/adr/ADR-0005-langgraph-staged-team-orchestration.yaml`
- `docs/ssot/adr/ADR-0006-config-layering-default-yaml-runtime.yaml`
- `docs/ssot/adr/ADR-0007-data-vendor-policy-tool-first-fallback.yaml`
