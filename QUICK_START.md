# 🚀 Quick Start Guide

## Current Status
✅ **Core working** - RSS scraper + backend + frontend verified  
✅ **Twitter scraper ready** - code complete, awaiting your build + auth

## Run the Working Stack

```bash
# Start everything (PostgreSQL, Redis, Backend, Celery, Frontend)
docker-compose up

# Or just backend + frontend
docker-compose up postgres redis backend frontend
```

Access:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **Database:** `postgresql://newsuser:newspass@localhost:5432/newsdb`

## What You'll See

- 42 RSS articles auto-scraped from Google News, Ars Technica, The Verge
- Search bar + category filters
- Stats dashboard
- Dark mode support
- Auto-refresh every 15 minutes

## Add Twitter Scraping

When ready:

1. **Build the Twitter container** (5-10 min first time):
   ```bash
   docker-compose build twitter-scraper
   ```

2. **(Optional) Add credentials** in `docker-compose.yml`:
   ```yaml
   twitter-scraper:
     environment:
       TWITTER_USERNAME: your_username
       TWITTER_PASSWORD: your_password
   ```

3. **Start it**:
   ```bash
   docker-compose up twitter-scraper
   ```

4. **See results**:
   ```bash
   docker logs -f news-twitter-scraper
   curl http://localhost:8000/api/news/?source=twitter
   ```

Full setup guide: `twitter-scraper/SETUP.md`

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
