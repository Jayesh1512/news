# 🚀 Quick Start Guide

## Current Status
✅ **Core working** - RSS scraper + backend + frontend verified  
❌ **Twitter scraper** - Build failed, not operational (use official API instead)

## Run the Working Stack

```bash
# Start everything (PostgreSQL, Redis, Backend, Celery, Frontend)
docker-compose up

# Or run in background
docker-compose up -d
```

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

The Twitter scraper **does not work** - Docker build fails on ARM64 system dependencies.

**Recommendation:** Use the official Twitter API instead.

See `twitter-scraper/STATUS.md` for:
- What went wrong
- Why it failed
- How to use Twitter API v2 (free tier available)
- Alternative approaches

## Stop Everything

```bash
docker-compose down
```

## Troubleshooting

**Frontend shows 500 error:**
```bash
docker-compose restart frontend
```

**No articles:**
```bash
# Trigger scraper manually
docker-compose exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"
```

**Celery not running:**
```bash
docker-compose logs celery-worker
docker-compose restart celery-worker celery-beat
```

---

**Full docs:** See README.md and IMPLEMENTATION_SUMMARY.md
