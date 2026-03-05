# Local LLM Runtime Guide (OpenAI-Compatible)

This fork supports local LLM serving without changing trading logic by using YAML config overrides.

## 1) Recommended: vLLM (OpenAI-Compatible API)

Example server startup:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model nvidia/Mistral-NeMo-12B-Instruct \
  --host 127.0.0.1 \
  --port 8000
```

Default config in this repo points to:
- `backend_url: http://127.0.0.1:8000/v1`

## 2) Alternative: Ollama (OpenAI-Compatible Endpoint)

Ollama OpenAI-compatible endpoint:
- `http://localhost:11434/v1`

If you use Ollama, either:
- set `llm_provider: "ollama"` in YAML, or
- keep `llm_provider: "openai"` and set `backend_url` to Ollama's endpoint.

## 3) Required Environment Variables

Some OpenAI-compatible client stacks still expect `OPENAI_API_KEY` to be present.

```bash
export OPENAI_API_KEY=dummy
```

You can keep using `.env` for local variables.

## 4) Run Commands

TradingAgents uses one `backend_url` for both quick/deep clients by default.
If your local server exposes only one model per endpoint, use the same model for both keys or run a multi-model endpoint.

Run via CLI with YAML config:

```bash
python -m cli.main --config configs/local_4090.yaml
```

Print effective merged config:

```bash
python -m cli.main --config configs/local_4090.yaml --print-effective-config
```

Run via root script using env-selected config:

```bash
export TRADINGAGENTS_CONFIG=configs/local_4090.yaml
python main.py
```
