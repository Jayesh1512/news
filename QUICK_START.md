# 🚀 Quick Start Guide

## Docker Compose Files

Each container lives in its own compose file so you can start exactly the
piece you need. Files that depend on another service `include:` it
automatically, so you always get a working stack even when you only name
one file. Database is Supabase (Postgres) - there's no local Postgres
container to start.

| File                                   | Starts                                                    |
| --------------------------------------- | ---------------------------------------------------------- |
| `docker-compose.redis.yml`              | redis                                                       |
| `docker-compose.backend.yml`            | + backend, celery-worker, celery-beat                       |
| `docker-compose.frontend.yml`           | + full backend stack, frontend                              |
| `docker-compose.twitter-scraper.yml`    | + full backend stack, twitter-scraper                       |
| `docker-compose.yml` (root)             | everything                                                  |

```bash
# Everything
docker compose up -d --build

# Just redis
docker compose -f docker-compose.redis.yml up -d

# Just the backend stack (brings up redis first)
docker compose -f docker-compose.backend.yml up -d --build

# Just the frontend (brings up the whole backend stack first)
docker compose -f docker-compose.frontend.yml up -d --build

# Stop only one service without touching the rest of the stack
docker compose -f docker-compose.frontend.yml stop frontend
```

All files share the same `news-network` and Compose project name (`news`),
so services started from different files can always reach each other by
service name, and `docker compose down` from the root removes everything.

**Before starting anything**, set up `.env` at the repo root (see
`backend/.env.example`): `DATABASE_URL` (Supabase Postgres connection
string) and `SUPABASE_URL`/`SUPABASE_KEY` are required.

Access:
- **Frontend:** http://localhost:8502
- **Backend API:** http://localhost:8501/docs
- **Redis:** `redis://localhost:8500/0`
- **Database:** Supabase (see your project dashboard, not a localhost URL)

## What You'll See

- RSS articles auto-scraped from Google News, Ars Technica, The Verge
- Twitter posts scraped every 6 hours from the accounts in
  `backend/app/core/constants.py`
- Search bar + category filters
- Stats dashboard
- Dark mode support
- Auto-refresh every 15 minutes

## Port Scheme

All ports are consecutive starting at **8500** (redis 8500, backend 8501,
frontend 8502) - see `PORTS.md` for details and how to change them.

For the exact command to run each container individually, see
[`CONTAINERS.md`](./CONTAINERS.md).

## About Twitter Scraping

The scraper container is built on [Agent-Reach](https://github.com/Panniantong/Agent-Reach)
/ `twitter-cli` - no browser, no Chromium. Requires `TWITTER_AUTH_TOKEN` /
`TWITTER_CT0` cookie auth - see `twitter-scraper/README.md` for setup.

## Stop Everything

```bash
docker compose down
```

## Troubleshooting

**Frontend shows 500 error:**
```bash
docker compose -f docker-compose.frontend.yml restart frontend
```

**No articles:**
```bash
# Trigger RSS scraper manually
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"

# Trigger Twitter scraper manually
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_twitter_accounts; print(scrape_twitter_accounts())"
```

**Celery not running:**
```bash
docker compose -f docker-compose.backend.yml logs celery-worker
docker compose -f docker-compose.backend.yml restart celery-worker celery-beat
```

**Backend can't connect to the database:**
- Check `DATABASE_URL` in `.env` - must be a valid Supabase Postgres
  connection string (Settings > Database > Connection string in your
  Supabase project)
- `docker compose -f docker-compose.backend.yml logs backend`

---

**Full docs:** See README.md and IMPLEMENTATION_SUMMARY.md
