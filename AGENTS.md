# TradingAgents Fork — Agent Instructions (SSOT-driven)

## Purpose
This repository is a fork of TauricResearch/TradingAgents.

Fork goals:
- Run reliably with a local LLM on an RTX 4090 (24GB VRAM).
- Keep changes minimal and backwards-compatible with upstream whenever possible.
- Introduce SSOT documentation, reproducible configs, and structured output contracts.

## Non-goals
- Do not turn this project into a real-money trading bot by default.
- Do not make investment advice claims in docs, comments, or PR descriptions.

## Working Agreement
- Keep changes minimal and backwards-compatible.
- Do NOT refactor unrelated code.
- Prefer small PRs with clear, testable acceptance criteria.
- If you must touch core runtime paths, explain why and keep the diff minimal.

## Code Style
- All comments and docstrings MUST be in English.
- New modules should use type hints.
- Keep dependencies minimal. Add a dependency only if justified in the PR.

## Repo Hygiene
- Never commit secrets: API keys, tokens, credential files, private URLs.
- Use `.env` for local secrets. Do not commit `.env`.
- Do not commit generated artifacts:
  - `results/`
  - `eval_results/`
  - `tradingagents/dataflows/data_cache/`

## Quick Checks Before Finishing
- Always run a quick sanity check before finishing:
  - `python -m compileall .`
- Optionally (if tests exist):
  - `pytest -q`

## How To Work With PR Prompts
- Restate scope in one paragraph before coding.
- Keep PR output focused on requested files and acceptance criteria.
- For docs-first PRs, avoid runtime import/path changes.
- End each PR with: changed files, checks run, and explicit out-of-scope items.

## Upstream Sync
Keep an `upstream` remote and sync regularly:
- `git fetch upstream --tags`
- `git merge upstream/main` (or rebase, if the PR requires a linear history)
