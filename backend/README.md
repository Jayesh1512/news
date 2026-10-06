# News Aggregator Backend

FastAPI backend for the news aggregator application.

## Features

- **Multi-source scraping**: RSS feeds and Twitter/X, stored in one JSON file
- **Background tasks**: Celery for scheduled scraping (RSS every 15 min, Twitter every 6h)
- **Storage**: Atomic, file-locked JSON at `data/news.json`
- **API**: RESTful API with automatic documentation

## Twitter/X scraping

Every `SCRAPE_TWITTER_INTERVAL_HOURS` (default 6h), the
`scrape_twitter_topic` Celery task searches `TWITTER_SEARCH_QUERY` via
[`twitter-cli`](https://github.com/jackwener/twitter-cli), upserts matching
posts, opens each match's conversation, and upserts all fetched replies.

The project runs twitter-cli through a local wrapper that redirects its
ClientTransaction bootstrap from X's stripped root page to the authenticated
`https://x.com/home` shell. It sends the already configured `auth_token` and
`ct0` cookies on that bootstrap request, implementing the focused upstream
fixes from `public-clis/twitter-cli#79` and `#91` without editing the installed
package.

Results are deduplicated by `tweet_id`; conversation replies are linked by
`root_tweet_id` and deduplicated by `reply_id`.

Read grouped results from `GET /api/twitter/threads`. Filter a stored topic
with `?search_query=<the exact configured query>`; each item contains a root
`post` and its associated `replies`.

**Setup:**

1. **Configure the topic**: set `TWITTER_SEARCH_QUERY` in `.env`. Normal X
   operators such as `lang:en` and `-filter:retweets` are supported.
2. **Configure credentials** in `.env` (see `.env.example`):
   - `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` (cookie auth for twitter-cli - see
     [`../twitter-scraper/README.md`](../twitter-scraper/README.md) for how
     to export these with Cookie-Editor)
3. Restart `celery-worker` and `celery-beat` (or the whole backend stack).

Trigger a run manually instead of waiting for the schedule:

```bash
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_twitter_topic; print(scrape_twitter_topic())"
```

If Twitter credentials aren't configured, the task returns
`{"status": "skipped", ...}` instead of failing.

### Topic profile discovery

The profile-analysis service collects every unique author found in a topic's
stored root posts and replies, fetches the latest 10-15 posts for each author,
and compares every post with `TWITTER_PROFILE_TOPIC_DESCRIPTION` using OpenAI
embeddings and cosine similarity. Results, including all analyzed posts and
the matching-post evidence and a structured, evidence-bound profile summary,
are stored in `twitter_profiles` inside `data/news.json`.

Configure `OPENAI_API_KEY` in the repo-root `.env`. The default embedding model
is `text-embedding-3-large` at 3,072 dimensions; it can be changed with
`TWITTER_PROFILE_EMBEDDING_MODEL`. Summaries default to `gpt-6-luna` and can be
changed with `TWITTER_PROFILE_SUMMARY_MODEL`.

Run the service directly:

```bash
docker compose -f docker-compose.backend.yml exec backend \
  python -m app.services.twitter_profile_analysis \
  --topic "Cheap LLM Providers" \
  --description "Affordable LLM APIs, inference providers, pricing comparisons, model routing, and reducing inference costs" \
  --posts-per-author 15 \
  --threshold 0.60
```

Run it as an independent Celery task:

```bash
docker compose -f docker-compose.backend.yml exec celery-worker \
  celery -A app.tasks.scrape call analyze_twitter_profiles \
  --kwargs='{"topic":"Cheap LLM Providers","posts_per_author":15,"similarity_threshold":0.60}'
```

To run automatically whenever topic posts are fetched, set
`TWITTER_PROFILE_ANALYSIS_AFTER_SCRAPE=true`. This works for both the Celery
topic scraper and batches ingested by the standalone scraper.

HTTP entry points:

- `POST /api/twitter/topic-searches` - generate semantic anchors and an X
  query from a user topic, then enqueue end-to-end discovery
- `GET /api/twitter/tasks/{task_id}` - poll discovery progress and results
- `POST /api/twitter/profiles/analyze` - enqueue through Celery or run inline
- `GET /api/twitter/profiles` - list profiles and filter by topic, minimum
  similarity, or minimum matching-post count

## Setup

### Prerequisites

- Python 3.12+
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

3. Update `.env` with `REDIS_URL` and optional X cookie credentials.

4. The backend creates `data/news.json` automatically on first startup.

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
- `GET /api/twitter/profiles` - Get topic-matched people and post evidence
- `POST /api/twitter/profiles/analyze` - Run or enqueue profile analysis
- `POST /api/twitter/topic-searches` - Generate context and start topic discovery
- `GET /api/twitter/tasks/{task_id}` - Read discovery progress

## API Documentation

Once running, visit (default Docker port 8501, see [`../PORTS.md`](../PORTS.md)):

- Swagger UI: http://localhost:8501/docs (or :8000/docs if running `uvicorn` directly, no Docker port mapping)
- ReDoc: http://localhost:8501/redoc

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
│   ├── core/             # Runtime configuration
│   ├── db/               # Atomic JSON datastore
│   ├── schemas/          # Pydantic schemas
│   ├── scrapers/         # Scraper implementations
│   ├── tasks/            # Celery tasks
│   └── main.py           # FastAPI application
├── Dockerfile
├── pyproject.toml        # UV configuration
└── .env.example
```
