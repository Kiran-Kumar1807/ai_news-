# AI-Powered Personalized News Aggregator

A production-ready platform that automatically collects news from RSS feeds,
categorizes and summarizes articles with the **Google Gemini API**, stores them
in **PostgreSQL**, and serves **personalized feeds** based on each user's
selected interests.

- **Backend:** FastAPI + SQLAlchemy + Alembic (JWT auth, REST API)
- **Frontend:** Streamlit (login, feed, article details, profile, analytics)
- **AI:** Gemini for categorization + 3-bullet summaries (heuristic fallback when no key)
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

> Without `GEMINI_API_KEY`, categorization/summarization use deterministic
> heuristic fallbacks so the app is fully functional for development and testing.

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
| GET    | `/health`                | —    | DB / Gemini / scheduler status     |

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

On every push / PR (`.github/workflows/ci.yml`):

1. Install dependencies
2. `ruff check` (lint)
3. `pytest` with coverage (fails under 80%)
4. Build backend & frontend Docker images
5. On `main`: trigger a Render deploy (if `RENDER_DEPLOY_HOOK_URL` secret is set)

---

## Deployment (free tier)

| Component | Service              | Notes                                            |
|-----------|----------------------|--------------------------------------------------|
| Database  | Supabase PostgreSQL  | Copy the connection string into `DATABASE_URL`.  |
| Backend   | Render (free web svc)| Build with `docker/Dockerfile.backend`; set env vars; start `alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. Add a Deploy Hook and store it as the `RENDER_DEPLOY_HOOK_URL` GitHub secret. |
| Frontend  | Streamlit Cloud      | Point at `frontend/app.py`; set `API_BASE_URL` to the Render backend URL. |
| Monitoring| UptimeRobot          | Ping `<backend>/health` every 5 minutes.         |

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
