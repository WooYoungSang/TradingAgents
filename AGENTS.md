# TradingAgents Fork — Agent Instructions (SSOT-driven)

## Purpose
This repository is a fork of TauricResearch/TradingAgents.
The fork’s goals:
- Run reliably with a local LLM on an RTX 4090 (24GB VRAM).
- Keep changes minimal and backwards-compatible with upstream whenever possible.
- Introduce SSOT documentation, reproducible configs, and structured output contracts.

## Non-goals
- Do not add features that turn this into a real-money trading bot by default.
- Do not provide investment advice claims in docs or code.

## How to Work in This Repo
- Prefer small PRs. Each PR must have:
  - A clear goal
  - A short checklist
  - Acceptance criteria
- Avoid refactors unrelated to the PR goal.

## Code Style
- All comments and docstrings MUST be in English.
- Prefer typed function signatures (type hints) for new modules.
- Keep dependencies minimal. Add a dependency only if it provides clear value and is justified in the PR.

## Safety & Secrets
- Never commit secrets (API keys, tokens, credentials files).
- Use .env for local secrets. Do not commit .env.
- Do not commit generated artifacts (results/, eval_results/, data cache).

## Local LLM Guidance (Non-China Models)
- Prefer non-China-origin open-weight models for English-centric workloads.
- Baseline recommendation:
  - quick_think_llm: Meta Llama 3.1 8B Instruct
  - deep_think_llm: Mistral Ministral 3 14B Instruct (or NVIDIA/Mistral NeMo 12B Instruct)
- Note: TradingAgents uses a single backend_url for both deep and quick clients by default.
  - If running different local models without code changes, prefer a multi-model server (e.g., Ollama OpenAI-compatible endpoint).
  - If using vLLM (typically one model per server), either run the same model for deep/quick or extend config to support separate base URLs.

## Required Checks Before Finishing Any PR
Run at least:
- python -m compileall .
Optionally (if tests exist):
- pytest -q

## Upstream Sync
Keep an upstream remote:
- git fetch upstream --tags
- git merge upstream/main (or rebase if project policy chooses)
