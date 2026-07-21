---
name: Testing the AI News Aggregator
description: How to run and end-to-end test the FastAPI + Streamlit AI news aggregator locally, including the multi-LLM router, TL;DR bulletins, Gemini quirks and known fallback bugs.
---

# Testing the AI News Aggregator

## Run locally (fast path, no Docker)
Use SQLite so no Postgres is needed. Both backend AND ingestion must share the same `DATABASE_URL`.

```bash
cd <repo>
# Run migrations on a FRESH sqlite DB to test the alembic path (do it once, cleanly —
# an interrupted run leaves half-created tables and the next run fails "table exists").
rm -f dev.db && DATABASE_URL='sqlite+pysqlite:///./dev.db' .venv/bin/alembic upgrade head
# Backend (scheduler + ingest-on-startup off keeps UI testing deterministic)
DATABASE_URL='sqlite+pysqlite:///./dev.db' GEMINI_API_KEY='<key>' \
  JWT_SECRET_KEY='test' ENABLE_SCHEDULER='false' INGEST_ON_STARTUP='false' \
  .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
# Ingest live RSS (needs network). NOTE: gemini_max_rpm=12 throttle => ~10s/article,
# so a full pass of ~40 articles takes 6-7 min. Poll /articles/analytics for progress.
DATABASE_URL='sqlite+pysqlite:///./dev.db' GEMINI_API_KEY='<key>' \
  .venv/bin/python -m ingestion.ingest
# Frontend
API_BASE_URL='http://localhost:8000' .venv/bin/streamlit run frontend/app.py \
  --server.port 8501 --server.headless true &
```

DB/heuristic inspection needs `PYTHONPATH=<repo>` set for standalone scripts importing `backend`/`ingestion`.
The session's `GEMINI_API_KEY` is present in the base shell env, so router uses Gemini even if you don't pass it explicitly; clear it (`GEMINI_API_KEY=''`) to force the heuristic path.

## UI navigation (Streamlit, frontend/app.py)
Sidebar radio "Go to". Unauthed: Login / Register. Authed: Feed / Article / Interests / Profile / Dashboard.
Golden path: Register → Login → Interests (check categories, Save) → Feed → View details → Profile → Dashboard.

## LLM router (PR #7+)
- `ingestion/llm.py` is a provider router; order `llm_provider_order` default `groq,gemini,openrouter`; only providers with a key configured run. Failover on error/rate-limit, then heuristic fallback.
- Default Gemini model is now `gemini-flash-lite-latest` (config.py) — **works on the free tier** (the old `gemini-1.5-flash` 404 issue is fixed); `gemini_max_rpm=12` throttle avoids 429s but makes bulk ingest slow (see above).
- `/health` now returns an **`llm`** component (NOT `gemini`): `status=ok, detail="providers: <list>"` when a key is set, else `status=disabled`. Overall status is `degraded` when llm is disabled (by design).
- Only a `GEMINI_API_KEY` is available in this env (no Groq/OpenRouter), so health shows `providers: gemini`.

## Bulletins + summaries (PR #7+)
- `summarizer.summarize_article()` returns `(bulletin, summary)`: a one-line TL;DR + a clean 3-bullet block. `articles.bulletin` column added by migration `0002_bulletin`.
- Frontend: feed shows bulletin in **bold** (`st.markdown(**...**)`) above the summary; article detail shows it via `st.info(...)` (blue box). Summaries render as a clean `<ul>` of exactly 3 `<li>`.
- Verify via DOM/screenshots that bullets have no stray `*`/`-`/`**`/backticks and there are exactly 3.

## Known bugs / edge cases to check
- Heuristic fallback classifier (`ingestion/classifier.py::classify_by_keywords`) uses substring `text.count("ai")` with no word boundaries → sports/politics articles (Argentina, captain, again…) get mislabeled "Artificial Intelligence". Expect a polluted feed when no LLM provider is available.
- Heuristic summary fallback (`summarize_by_sentences`) uses `_format_bullets(sentences[:3])`, so very short content (1-2 sentences) yields **fewer than 3 bullets**. Real Gemini output always gives exactly 3. Only matters on the no-provider path with short RSS text.

## Devin Secrets Needed
- `GEMINI_API_KEY` — to exercise the real AI path (categorization/summarization). App works without it via heuristics.

## Notes
- Unauth `/feed` returns 403 (FastAPI HTTPBearer default), not 401.
- Categories endpoint returns 10 canonical categories (backend/core/categories.py).
