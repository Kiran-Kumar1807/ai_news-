# AI-Powered Personalized News Aggregator

A production-ready platform that automatically collects news from RSS feeds,
categorizes and summarizes articles with the **Google Gemini API**, stores them
in **PostgreSQL**, and serves **personalized feeds** based on each user's
selected interests.

- **Backend:** FastAPI + SQLAlchemy + Alembic (JWT auth, REST API)
- **Frontend:** Streamlit (login, feed, article details, profile, analytics)
- **AI:** multi-provider LLM router (Groq / Gemini / OpenRouter) for categorization, a one-line **TL;DR bulletin** + clean 3-bullet summaries; fails over between providers on rate-limit and falls back to heuristics when no key
- **Ingestion:** `feedparser` RSS collection with SHA-256 deduplication
- **Scheduler:** APScheduler — hourly ingestion + daily email digest (Gmail SMTP)
- **Infra:** Docker Compose, GitHub Actions CI/CD, structured logging, health checks

---

## Architecture

```
                +-------------------+        +--------------------+
   RSS feeds -->|  Ingestion (hourly)|------>|   PostgreSQL       |
                |  fetch/dedupe/AI   |       |  users, niches,    |
                +-------------------+        |  preferences,      |
                                             |  articles          |
   Streamlit  <--- REST/JWT --- FastAPI ---> |                    |
   frontend                     backend      +--------------------+
                                   |
                          APScheduler (daily digest -> Gmail SMTP)
```

## Project structure

```
ai_news_aggregator/
├── backend/
│   ├── api/            # FastAPI routers + auth dependencies
│   ├── services/       # business logic (auth, users, articles, feed)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic models
│   ├── database/       # engine, session, base
│   ├── core/           # categories & keywords
│   ├── config.py       # settings (env vars)
│   └── main.py         # FastAPI app + lifespan
├── frontend/           # Streamlit app + API client
├── ingestion/          # rss_fetcher, article_extractor, classifier, summarizer
├── scheduler/          # APScheduler jobs + daily_digest + email client
├── alembic/            # migrations
├── tests/              # pytest suite (>=80% coverage gate)
├── docker/             # backend & frontend Dockerfiles
├── docker-compose.yml
└── .github/workflows/  # CI/CD
```

---

## Quick start (Docker)

```bash
git clone <your-repo-url> ai_news_aggregator
cd ai_news_aggregator
docker compose up --build
```

Services:

| Service   | URL                          |
|-----------|------------------------------|
| Backend   | http://localhost:8000        |
| API docs  | http://localhost:8000/docs   |
| Frontend  | http://localhost:8501        |
| Postgres  | localhost:5432               |

The stack runs **without any configuration**. To enable AI and email features,
export variables before `docker compose up` (or put them in a `.env` file — see
`.env.example`):

```bash
export GEMINI_API_KEY=your_key
export SMTP_USERNAME=you@gmail.com
export SMTP_PASSWORD=your_gmail_app_password
```

> Without any LLM key, categorization/summarization use deterministic
> heuristic fallbacks so the app is fully functional for development and testing.

### Multiple free LLM providers (avoid rate limits)

The app routes AI calls through several free-tier providers and switches to the
next one the moment one is rate-limited, so combined quotas give near-seamless
service. Enable any subset by setting their keys:

```bash
export GROQ_API_KEY=...        # https://console.groq.com/keys (fast, generous free tier)
export OPENROUTER_API_KEY=...  # https://openrouter.ai/keys (free Llama models)
export GEMINI_API_KEY=...      # https://aistudio.google.com/apikey
# Order tried (only providers with a key run):
export LLM_PROVIDER_ORDER=groq,gemini,openrouter
```

---

## Local development (without Docker)

Requires Python 3.10+ and a PostgreSQL instance (or use SQLite for a quick run).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit as needed

# Run migrations (Postgres). For a quick spin you can point DATABASE_URL at SQLite.
alembic upgrade head

# Start the API
uvicorn backend.main:app --reload

# In another terminal, start the frontend
API_BASE_URL=http://localhost:8000 streamlit run frontend/app.py
```

Run ingestion manually:

```bash
python -m ingestion.ingest
```

Send the daily digest manually:

```bash
python -m scheduler.daily_digest
```

---

## API endpoints

| Method | Path                     | Auth | Description                        |
|--------|--------------------------|------|------------------------------------|
| POST   | `/register`              | —    | Create a user                      |
| POST   | `/login`                 | —    | Obtain a JWT access token          |
| GET    | `/profile`               | JWT  | Current user + interests           |
| POST   | `/preferences`           | JWT  | Replace selected interests         |
| GET    | `/feed`                  | JWT  | Personalized feed (latest first)   |
| GET    | `/articles/{id}`         | —    | Full article detail                |
| GET    | `/articles/analytics`    | —    | Dashboard analytics                |
| GET    | `/categories`            | —    | Supported categories               |
| GET    | `/health`                | —    | DB / LLM providers / scheduler     |

---

## Testing

```bash
pytest --cov --cov-report=term-missing --cov-fail-under=80
```

Tests use an in-memory SQLite database and cover authentication, summarization,
categorization, feed generation and database operations. Linting is enforced
with `ruff`:

```bash
ruff check .
```

---

## CI/CD (GitHub Actions)

> The workflow lives at `docs/ci.yml` in this repo and must be moved to
> `.github/workflows/ci.yml` with a workflow-scoped token to activate it
> (see `docs/CI_CD.md`).

On every push / PR:

1. Install dependencies
2. `ruff check` (lint)
3. `pytest` with coverage (fails under 80%)
4. Build backend & frontend Docker images
5. On `main`: trigger a Render deploy (if `RENDER_DEPLOY_HOOK_URL` secret is set)

---

## Deployment

### One-click Render Blueprint (recommended)

The repo ships a [`render.yaml`](render.yaml) Blueprint that provisions everything:
a managed PostgreSQL database, the FastAPI backend (with the APScheduler jobs),
and the Streamlit frontend.

1. In the Render Dashboard: **New + → Blueprint**, and select this repo.
2. Render creates `ai-news-db`, `ai-news-backend`, and `ai-news-frontend`.
   `DATABASE_URL` is wired from the database and `JWT_SECRET_KEY` is
   auto-generated.
3. Set the `sync: false` secrets when prompted:
   - Backend: `GEMINI_API_KEY` (and optional `SMTP_*`).
   - After the first deploy, set the cross-service URLs:
     - Backend `CORS_ORIGINS` → the frontend URL (e.g. `https://ai-news-frontend.onrender.com`).
     - Frontend `API_BASE_URL` → the backend URL (e.g. `https://ai-news-backend.onrender.com`).
   Then trigger a redeploy of both services.
4. Add a UptimeRobot HTTP monitor on `<backend>/health` every 5 minutes. On the
   free tier this also keeps the backend awake so the hourly ingestion job fires.

The backend runs `alembic upgrade head` on boot and serves via
`gunicorn` + Uvicorn workers. It uses a **single worker** so only one
APScheduler instance runs (avoiding duplicate ingestion/digest jobs).

> Free-tier notes: Render free web services sleep after inactivity — the
> UptimeRobot ping keeps the backend warm. The free Postgres instance expires
> after ~30 days. For real production traffic, use paid instances and move the
> scheduler to a dedicated worker or Render Cron Job.

### Alternatives

| Component | Service              | Notes                                            |
|-----------|----------------------|--------------------------------------------------|
| Database  | Supabase PostgreSQL  | Copy the connection string into `DATABASE_URL` (the app normalizes `postgres://` automatically). |
| Frontend  | Streamlit Cloud      | Point at `frontend/app.py`; set `API_BASE_URL` to the backend URL. |
| CI deploy | GitHub Actions       | Set the `RENDER_DEPLOY_HOOK_URL` secret to auto-trigger a Render deploy on `main`. |

### Environment variables

See `.env.example` for the full list. Key ones:

- `DATABASE_URL` — SQLAlchemy connection string
- `JWT_SECRET_KEY` — long random secret for signing tokens
- `GEMINI_API_KEY`, `GEMINI_MODEL` — AI configuration
- `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` — Gmail SMTP for digests
- `INGEST_INTERVAL_MINUTES`, `DIGEST_HOUR`, `ENABLE_SCHEDULER` — scheduling

---

## Coding standards

Type hints throughout, dependency injection via FastAPI, service layer for
reusable business logic, Pydantic validation, environment-based config,
structured JSON logging, and docstrings on public functions.
