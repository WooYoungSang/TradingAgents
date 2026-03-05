# SSOT for TradingAgents Fork

## 1) Fork Goals
This fork defines a Single Source of Truth (SSOT) for planned changes while preserving upstream behavior.

Primary goals:
- Reliable local execution on RTX 4090 (24GB VRAM).
- Reproducible runs via explicit configuration and documented run procedures.
- Structured output contract for downstream consumers (`TradePlan`, planned).

## 2) Scope and Out-of-Scope
In scope for SSOT:
- Documentation standards and ADR policy.
- Configuration contract documentation for current `DEFAULT_CONFIG`.
- Baseline run and logging conventions.

Out-of-scope for PR-1:
- Runtime logic changes to agent orchestration or decision flow.
- Refactors unrelated to SSOT setup.
- New dependencies.

## 3) Upstream Architecture Baseline (High-Level)
Current baseline follows upstream structure:
- Core orchestration: `TradingAgentsGraph` in `tradingagents/graph/trading_graph.py`.
- Runtime defaults: `DEFAULT_CONFIG` in `tradingagents/default_config.py`.
- Entry points:
  - `main.py` for script execution.
  - `python -m cli.main` for interactive CLI flow.

## 4) Planned Phases
- PR-2: YAML config layer (non-breaking) mapped to current config dict.
- PR-3: Output contract introduction (`TradePlan.v1`) with validation boundary.
- PR-4: Logging and run metadata normalization for reproducibility.
- PR-5: Integration polish, docs hardening, and compatibility checks against upstream.

## ADR Index
- ADR-0002: Local LLM standard = OpenAI-compatible server (vLLM)

## 5) Config Contract (Current)
`DEFAULT_CONFIG` keys currently used by runtime:
- `project_dir`
- `results_dir`
- `data_cache_dir`
- `llm_provider`
- `deep_think_llm`
- `quick_think_llm`
- `backend_url`
- `google_thinking_level`
- `openai_reasoning_effort`
- `max_debate_rounds`
- `max_risk_discuss_rounds`
- `max_recur_limit`
- `data_vendors`
- `tool_vendors`

Standard for this fork (as of PR-2):
- YAML config is the preferred user-facing format.
- Runtime still preserves backwards compatibility by merging YAML overrides onto `DEFAULT_CONFIG`.
- Existing code paths using `DEFAULT_CONFIG.copy()` remain valid.

`data_vendors` category keys:
- `core_stock_apis`
- `technical_indicators`
- `fundamental_data`
- `news_data`

Planned extensions (PR-2+):
- YAML config files loaded into this same contract.
- Optional split endpoints for deep/quick LLM backends.
- Config versioning field for migration safety.

## 6) Output Contract Placeholder: `TradePlan.v1`
Status: placeholder for later implementation.

Planned minimum fields:
- `schema_version` (e.g., `TradePlan.v1`)
- `ticker`
- `trade_date`
- `decision` (`BUY` | `SELL` | `HOLD`)
- `confidence` (0.0-1.0)
- `rationale_summary`
- `risk_notes`
- `sources` (high-level provenance only)

## 7) Logging Contract (Current + Convention)
Current runtime writes:
- Graph state logs to `eval_results/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json`
- CLI session artifacts under `results/<TICKER>/<DATE>/...`

Conventions for this fork:
- Keep all generated run artifacts under `results/` and `eval_results/`.
- Use date-based names (`YYYY-MM-DD`) and stable snake_case file names.
- Do not commit generated outputs to git.
