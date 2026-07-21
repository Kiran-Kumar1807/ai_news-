---
name: Testing the AI News Aggregator
description: How to run and end-to-end test the FastAPI + Streamlit AI news aggregator locally, including Gemini quirks and known fallback bugs.
---

# Testing the AI News Aggregator

## Run locally (fast path, no Docker)
Use SQLite so no Postgres is needed. Both backend AND ingestion must share the same `DATABASE_URL`.

```bash
cd <repo>
# Backend (scheduler off keeps UI testing deterministic)
DATABASE_URL='sqlite+pysqlite:///./dev.db' GEMINI_API_KEY='<key>' GEMINI_MODEL='gemini-2.5-flash' \
  JWT_SECRET_KEY='test' ENABLE_SCHEDULER='false' \
  .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
# Ingest live RSS (needs network; ~30–60s; stores ~90 articles)
DATABASE_URL='sqlite+pysqlite:///./dev.db' GEMINI_API_KEY='<key>' GEMINI_MODEL='gemini-2.5-flash' \
  .venv/bin/python -m ingestion.ingest
# Frontend
API_BASE_URL='http://localhost:8000' .venv/bin/streamlit run frontend/app.py \
  --server.port 8501 --server.headless true &
```

## UI navigation (Streamlit, frontend/app.py)
Sidebar radio "Go to". Unauthed: Login / Register. Authed: Feed / Article / Interests / Profile / Dashboard.
Golden path: Register → Login → Interests (check categories, Save) → Feed → View details → Profile → Dashboard.

## Gemini gotchas (important)
- Config default model is `gemini-1.5-flash`, which **404s on newer free API keys**. Override with `GEMINI_MODEL=gemini-2.5-flash` (or list models via `genai.list_models()`).
- Free tier = **5 requests/min**. Ingestion makes 2 calls/article (classify+summarize), so bulk ingest quickly hits `429` and **silently falls back to heuristics**. Don't expect real AI output across a full corpus; prove the AI path with a single isolated call instead.
- `/health` reports `gemini=ok` whenever a key is set — it does NOT verify the model actually works.

## Known bug to check
- Heuristic fallback classifier (`ingestion/classifier.py::classify_by_keywords`) uses substring `text.count("ai")` with no word boundaries → sports/politics articles (Argentina, captain, again…) get mislabeled "Artificial Intelligence". Expect a polluted feed when Gemini is unavailable.

## Devin Secrets Needed
- `GEMINI_API_KEY` — to exercise the real AI path (categorization/summarization). App works without it via heuristics.

## Notes
- Unauth `/feed` returns 403 (FastAPI HTTPBearer default), not 401.
- Categories endpoint returns 10 canonical categories (backend/core/categories.py).
