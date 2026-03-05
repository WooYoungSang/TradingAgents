# Configs Directory

This directory contains YAML runtime configs introduced in PR-2.

Current state:
- Runtime baseline remains `tradingagents/default_config.py` (`DEFAULT_CONFIG`).
- YAML overrides are loaded by `tradingagents/config_loader.py`.

Naming conventions:
- `local_4090.yaml`: local development and 24GB VRAM profile.
- `cloud_eval.yaml`: cloud or CI-style evaluation profile.

Guidelines:
- Keep keys aligned with the documented config contract in `docs/SSOT.md`.
- Add migration notes when introducing new keys or defaults.

CLI usage:
```bash
python -m cli.main --config configs/local_4090.yaml
python -m cli.main --config configs/local_4090.yaml --print-effective-config
```

Root `main.py` usage:
- Set `TRADINGAGENTS_CONFIG=/path/to/config.yaml` to override defaults.
- If not set, `configs/local_4090.yaml` is used when present.
- If neither is available, the legacy hardcoded example config is used.

Experiment usage:
```bash
python eval/run_experiment.py \
  --config configs/local_4090.yaml \
  --symbols "AAPL,MSFT" \
  --dates "2026-01-01:2026-01-03"

python eval/run_experiment.py \
  --config configs/cloud_eval.yaml \
  --symbols "AAPL,MSFT" \
  --dates "2026-01-01:2026-01-03"
```
