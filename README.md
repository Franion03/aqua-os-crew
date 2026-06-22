# 🤖 aqua-os-crew

AI agent crews for water polo club operations — match prep, enrollment, progress reviews, and more.

## Architecture

Python FastAPI service running CrewAI agents via OpenRouter/Gemini LLMs. Each crew handles a specific domain of club operations.

```
crews/
  match_prep/          → pre-game analysis & strategy
  enrollment/          → new player onboarding
  progress_review/     → player development tracking
  season_plan/         → season scheduling & goals
  injury_response/     → injury management workflows
tools/
  calendar_tool.py     → calendar integration tool
main.py                → FastAPI entrypoint
```

## Prerequisites

- Python 3.11+
- OpenRouter API key or Gemini API key

## Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --port 8001
```

Server starts on **http://localhost:8001**

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | One of these |
| `GEMINI_API_KEY` | Google Gemini API key | One of these |

## Docker

```bash
docker build -t aqua-os-crew .
docker run -p 8001:8001 -e OPENROUTER_API_KEY=sk-... aqua-os-crew
```

## Related Repos

| Repo | Description |
|------|-------------|
| [aqua-os-backend](../aqua-os-backend) | Go REST API |
| [aqua-os-web](../aqua-os-web) | React frontend |
| [aqua-os-calendar](../aqua-os-calendar) | Game calendar service |
| [aqua-os-infrastructure](../aqua-os-infrastructure) | Terraform AWS infra |

## License

GPL-3.0

## Metrics

Prometheus metrics are available via `metrics.py`. To enable, call in your FastAPI app:

```python
from metrics import setup_metrics
setup_metrics(app)
```

Exposes auto-instrumented HTTP metrics at `/metrics`.
