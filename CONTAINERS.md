# Containers

Exact commands to build and run each container in this project, both via
Docker Compose (recommended - handles networking, env vars, and
dependencies for you) and as standalone `docker run` commands.

Database is [Supabase](https://supabase.com) (Postgres + REST API), not a
container - there's no local Postgres to start. Before running anything,
create a `.env` file at the repo root (see
[`backend/.env.example`](./backend/.env.example) for the full list):

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.<project>.supabase.co:5432/postgres
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<service_role key>
TWITTER_AUTH_TOKEN=<auth_token cookie>
TWITTER_CT0=<ct0 cookie>
```

Ports are consecutive starting at **8500** - see [`PORTS.md`](./PORTS.md).

---

## Everything at once

```bash
docker compose up -d --build
```

Stop everything:

```bash
docker compose down
```

---

## Redis

Broker/result backend for Celery. No build needed (uses the official image).

**Compose (recommended):**
```bash
docker compose -f docker-compose.redis.yml up -d
```

**Standalone `docker run`:**
```bash
docker run -d --name news-redis -p 8500:6379 redis:7-alpine
```

---

## Backend (FastAPI)

Depends on: Redis, Supabase (external). Also needs `DATABASE_URL`,
`SUPABASE_URL`, `SUPABASE_KEY` from `.env`.

**Compose (recommended - brings up Redis automatically):**
```bash
docker compose -f docker-compose.backend.yml up -d --build backend
```

**Standalone `docker run`** (requires Redis reachable at the URL you pass):
```bash
docker build -t news-backend ./backend
docker run -d --name news-backend -p 8501:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  -e REDIS_URL="redis://host.docker.internal:8500/0" \
  -e CORS_ORIGINS="http://localhost:8502" \
  news-backend
```

Access: http://localhost:8501 (docs: http://localhost:8501/docs)

---

## Celery worker

Executes scheduled scrape tasks. Same image as the backend, different command.

**Compose (recommended):**
```bash
docker compose -f docker-compose.backend.yml up -d --build celery-worker
```

**Standalone `docker run`:**
```bash
docker build -t news-backend ./backend
docker run -d --name news-celery-worker \
  -e DATABASE_URL="$DATABASE_URL" \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  -e REDIS_URL="redis://host.docker.internal:8500/0" \
  news-backend \
  celery -A app.tasks.scrape worker --loglevel=info
```

---

## Celery beat

Triggers scheduled tasks (RSS every 15 min, Twitter every 6h). Same image
as the backend, different command.

**Compose (recommended):**
```bash
docker compose -f docker-compose.backend.yml up -d --build celery-beat
```

**Standalone `docker run`:**
```bash
docker build -t news-backend ./backend
docker run -d --name news-celery-beat \
  -e DATABASE_URL="$DATABASE_URL" \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  -e REDIS_URL="redis://host.docker.internal:8500/0" \
  news-backend \
  celery -A app.tasks.scrape beat --loglevel=info
```

---

## Frontend (Next.js)

Depends on: Backend (for the API).

**Compose (recommended - brings up the full backend stack automatically):**
```bash
docker compose -f docker-compose.frontend.yml up -d --build frontend
```

**Standalone `docker run`:**
```bash
docker build -t news-frontend ./frontend \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8501
docker run -d --name news-frontend -p 8502:3000 \
  -e NEXT_PUBLIC_API_URL="http://localhost:8501" \
  -e API_URL_SERVER="http://host.docker.internal:8501" \
  news-frontend
```

Access: http://localhost:8502

---

## Twitter scraper

Given a list of X/Twitter profile URLs, fetches each profile's most recent
posts and POSTs them to the backend. Built on
[Agent-Reach](https://github.com/Panniantong/Agent-Reach) / `twitter-cli` -
needs `TWITTER_AUTH_TOKEN`/`TWITTER_CT0` cookie auth (see
[`twitter-scraper/README.md`](./twitter-scraper/README.md)). No host port.

**Compose (recommended - brings up the full backend stack automatically):**
```bash
docker compose -f docker-compose.twitter-scraper.yml up -d --build twitter-scraper
```

**Standalone `docker run`** (requires the backend reachable at `BACKEND_URL`):
```bash
docker build -t news-twitter-scraper ./twitter-scraper
docker run -d --name news-twitter-scraper \
  -e BACKEND_URL="http://host.docker.internal:8501" \
  -e TWITTER_PROFILE_URLS="https://x.com/elonmusk,https://x.com/OpenAI" \
  -e TWITTER_AUTH_TOKEN="$TWITTER_AUTH_TOKEN" \
  -e TWITTER_CT0="$TWITTER_CT0" \
  news-twitter-scraper
```

Run a single scrape pass instead of the loop:
```bash
docker compose -f docker-compose.twitter-scraper.yml run --rm twitter-scraper python -u scraper.py --once
```

---

## Useful one-offs

Trigger a scrape manually (via the running backend container):
```bash
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_twitter_accounts; print(scrape_twitter_accounts())"
```

Check Agent-Reach's Twitter channel health from inside the scraper container:
```bash
docker compose -f docker-compose.twitter-scraper.yml exec twitter-scraper agent-reach doctor
```

Tail logs for any service:
```bash
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f celery-beat
docker compose logs -f frontend
docker compose logs -f twitter-scraper
docker compose logs -f redis
```

Stop one service without touching the rest:
```bash
docker compose -f docker-compose.frontend.yml stop frontend
```

Rebuild after code changes:
```bash
docker compose up -d --build <service>
```
