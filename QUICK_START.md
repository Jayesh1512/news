# 🚀 Quick Start Guide

## Docker Compose Files

Each container lives in its own compose file so you can start exactly the
piece you need. Files that depend on another service `include:` it
automatically, so you always get a working stack even when you only name
one file.

| File                                   | Starts                                                    |
| --------------------------------------- | ---------------------------------------------------------- |
| `docker-compose.postgres.yml`           | postgres                                                    |
| `docker-compose.redis.yml`              | redis                                                       |
| `docker-compose.backend.yml`            | + backend, celery-worker, celery-beat                       |
| `docker-compose.frontend.yml`           | + full backend stack, frontend                              |
| `docker-compose.twitter-scraper.yml`    | + full backend stack, twitter-scraper                       |
| `docker-compose.yml` (root)             | everything                                                  |

```bash
# Everything
docker compose up -d --build

# Just the database
docker compose -f docker-compose.postgres.yml up -d

# Just the backend stack (brings up postgres + redis first)
docker compose -f docker-compose.backend.yml up -d --build

# Just the frontend (brings up the whole backend stack first)
docker compose -f docker-compose.frontend.yml up -d --build

# Stop only one service without touching the rest of the stack
docker compose -f docker-compose.frontend.yml stop frontend
```

All files share the same `news-network` and Compose project name (`news`),
so services started from different files can always reach each other by
service name, and `docker compose down` from the root removes everything.

Access:
- **Frontend:** http://localhost:3001 (changed from 3000 due to port conflicts)
- **Backend API:** http://localhost:8001/docs (changed from 8000)
- **Database:** `postgresql://newsuser:newspass@localhost:5432/newsdb`

## What You'll See

- 42 RSS articles auto-scraped from Google News, Ars Technica, The Verge
- Search bar + category filters
- Stats dashboard
- Dark mode support
- Auto-refresh every 15 minutes

## Port Changes

**Due to OrbStack conflicts, ports have changed:**
- Frontend: 3000 → **3001**
- Backend: 8000 → **8001**
- Redis: 6379 → **6380**

See `PORTS.md` for details.

## About Twitter Scraping

The scraper container builds on Microsoft's official Playwright image and
starts alongside the rest of the stack. It needs Twitter auth for anything
beyond public timelines - see `twitter-scraper/README.md` for setup.

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
# Trigger scraper manually
docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"
```

**Celery not running:**
```bash
docker compose -f docker-compose.backend.yml logs celery-worker
docker compose -f docker-compose.backend.yml restart celery-worker celery-beat
```

---

**Full docs:** See README.md and IMPLEMENTATION_SUMMARY.md
