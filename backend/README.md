# News Aggregator Backend

FastAPI backend for the news aggregator application.

## Features

- **Multi-source scraping**: RSS feeds (Postgres), Twitter/X (Supabase)
- **Background tasks**: Celery for scheduled scraping
- **Database**: PostgreSQL with SQLAlchemy ORM (RSS articles) + Supabase (Twitter posts)
- **API**: RESTful API with automatic documentation

## Twitter/X scraping (Supabase)

Every `SCRAPE_TWITTER_INTERVAL_HOURS` (default 6h), the `scrape_twitter_accounts`
Celery task fetches recent posts for each account in
[`app/core/constants.py`](app/core/constants.py) `TWITTER_ACCOUNTS` via
[`twitter-cli`](https://github.com/jackwener/twitter-cli) and upserts them
into a Supabase table (deduped by `tweet_id`).

**Setup:**

1. **Edit the account list**: `app/core/constants.py` → `TWITTER_ACCOUNTS`
   (bare handles, no `@`).
2. **Create the Supabase table**: run [`supabase_schema.sql`](supabase_schema.sql)
   in your Supabase project's SQL editor.
3. **Configure credentials** in `.env` (see `.env.example`):
   - `SUPABASE_URL` / `SUPABASE_KEY` (service_role key - from Supabase
     project Settings > API)
   - `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` (cookie auth for twitter-cli - see
     [`../twitter-scraper/README.md`](../twitter-scraper/README.md) for how
     to export these with Cookie-Editor)
4. Restart `celery-worker` and `celery-beat` (or the whole backend stack).

Trigger a run manually instead of waiting for the schedule:

```bash
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_twitter_accounts; print(scrape_twitter_accounts())"
```

If Supabase or Twitter credentials aren't configured, the task returns
`{"status": "skipped", ...}` instead of failing.

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- UV package manager

### Installation

1. Install dependencies with UV:

```bash
cd backend
uv pip install -r pyproject.toml
```

2. Copy environment file:

```bash
cp .env.example .env
```

3. Update `.env` with your database and Redis URLs

4. Run database migrations:

```bash
uv run alembic upgrade head
```

5. Start the API server:

```bash
uvicorn app.main:app --reload
```

6. Start Celery worker (in another terminal):

```bash
celery -A app.tasks.scrape worker --loglevel=info
```

7. Start Celery beat scheduler (in another terminal):

```bash
celery -A app.tasks.scrape beat --loglevel=info
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/news` - Get news articles (with filters)
- `GET /api/news/stats` - Get statistics
- `GET /api/news/search?q=query` - Search articles
- `GET /api/sources` - Get all sources
- `GET /api/sources/active` - Get active sources

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker

Build and run with Docker:

```bash
docker build -t news-backend .
docker run -p 8000:8000 --env-file .env news-backend
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Configuration + constants (TWITTER_ACCOUNTS)
│   ├── db/               # Database setup (Postgres session + Supabase client)
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── scrapers/         # Scraper implementations
│   ├── tasks/            # Celery tasks
│   └── main.py           # FastAPI application
├── Dockerfile
├── pyproject.toml        # UV configuration
├── supabase_schema.sql   # Twitter posts table DDL
└── .env.example
```
