# Configs Directory (Planned)

This directory is reserved for YAML-based runtime configs introduced in PR-2.

Current state:
- Runtime still uses `tradingagents/default_config.py` (`DEFAULT_CONFIG`).
- No YAML loader is active in PR-1.

Planned naming conventions:
- `local_4090.yaml`: local development and 24GB VRAM profile.
- `cloud_eval.yaml`: cloud or CI-style evaluation profile.

Guidelines:
- Keep keys aligned with the documented config contract in `docs/SSOT.md`.
- Add migration notes when introducing new keys or defaults.
