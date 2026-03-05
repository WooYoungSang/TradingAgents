# Baseline Run (Commands Only)

## Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Entry Point: Script (`main.py`)
```bash
python main.py
```

## Entry Point: CLI
```bash
python -m cli.main
```

## Quick Sanity Check
```bash
python -m compileall .
```

## Optional Tests
```bash
pytest -q
```

## Upstream Sync (Reference)
```bash
git fetch upstream --tags
git merge upstream/main
```
