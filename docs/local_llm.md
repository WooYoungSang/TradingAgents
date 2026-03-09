# Local LLM Runtime Guide (OpenAI-Compatible)

This fork supports local LLM serving without changing trading logic by using YAML config overrides.
Keep the runtime contract simple:

- `llm_provider` stays `"openai"` for OpenAI-compatible local servers.
- `backend_url` points to the server's `/v1` endpoint.
- `quick_think_llm` and `deep_think_llm` must name models that the same endpoint can actually serve.

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
- `quick_think_llm: nvidia/Mistral-NeMo-12B-Instruct`
- `deep_think_llm: nvidia/Mistral-NeMo-12B-Instruct`

The default profile keeps both model keys on the same model so one local server can work out of the box.
Only split the quick/deep model names if your OpenAI-compatible endpoint exposes multiple model IDs behind the same `backend_url`.

## 2) Alternative: Ollama (OpenAI-Compatible Endpoint)

Ollama OpenAI-compatible endpoint:
- `http://localhost:11434/v1`

If you use Ollama, keep `llm_provider: "openai"` and update:

- `backend_url` to Ollama's `/v1` endpoint
- `quick_think_llm` to an Ollama model tag served by that endpoint
- `deep_think_llm` to the same tag unless you intentionally expose multiple served models

## 3) Required Environment Variables

Some OpenAI-compatible client stacks still expect `OPENAI_API_KEY` to be present.

```bash
export OPENAI_API_KEY=dummy
```

You can keep using `.env` for local variables.

## 4) Run Commands

TradingAgents uses one `backend_url` for both quick/deep clients by default.
That is why `configs/local_4090.yaml` keeps both model keys aligned to one served model by default.

Run via CLI with YAML config:

```bash
python -m cli.main --config configs/local_4090.yaml
```

Print effective merged config:

```bash
python -m cli.main --config configs/local_4090.yaml --print-effective-config
```

Run via root script using an explicit env-selected config:

```bash
export OPENAI_API_KEY=dummy
export TRADINGAGENTS_CONFIG=configs/local_4090.yaml
python main.py
```

For a reproducible local session, exporting both variables before either command is recommended:

```bash
export OPENAI_API_KEY=dummy
export TRADINGAGENTS_CONFIG=configs/local_4090.yaml
python -m cli.main --config configs/local_4090.yaml --print-effective-config
```
