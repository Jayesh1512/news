# System Status

## Working Components ✅

- **RSS Scraper**: Fully operational, actively scraping articles
- **PostgreSQL Database**: Running and storing articles
- **Redis**: Running on port 6380
- **FastAPI Backend**: Serving at http://localhost:8001
- **Next.js Frontend**: Serving at http://localhost:3001
- **Celery Workers**: Processing scheduled tasks
- **Twitter Scraper**: Builds and runs (fixed 2026-08-16, see below)

## Twitter Scraper - RESOLVED (2026-08-16)

**Original failure** (2026-08-14, kept for reference):

```bash
$ docker compose build twitter-scraper
Error: Installation process exited with code: 100
failed to solve: process "playwright install-deps chromium" did not complete successfully: exit code: 1
Result: ❌ BUILD FAILED
```

**Root cause**: `playwright install-deps chromium` on `python:3.11-slim`
(Debian Trixie) tries to apt-install `ttf-unifont` / `ttf-ubuntu-font-family`,
which don't exist under those names on Trixie.

**Fix**: switched the base image to `mcr.microsoft.com/playwright/python`,
Microsoft's official image with Chromium and all OS-level dependencies
already installed and version-matched to the `playwright` pip package. No
apt install step needed at all.

**Verification** (2026-08-16):
```bash
$ docker compose -f docker-compose.twitter-scraper.yml build twitter-scraper
 Image news-twitter-scraper Built
Result: ✅ BUILD SUCCEEDED

$ docker compose -f docker-compose.twitter-scraper.yml up -d
 Container news-twitter-scraper Started
$ docker ps --filter name=news-twitter-scraper
news-twitter-scraper   Up (healthy)
Result: ✅ RUNTIME OK
```

Anonymous scraping is still rate-limited by Twitter/X; for reliable
production use, set `TWITTER_AUTH_TOKEN`/`TWITTER_CT0` (see
`twitter-scraper/.env.example`) or switch to Twitter API v2.

## Architecture

The system is split into independently-deployable services, each with its
own `docker-compose.*.yml`:
- `docker-compose.postgres.yml` / `docker-compose.redis.yml` - data stores
- `docker-compose.backend.yml` - FastAPI + Celery worker + Celery beat
- `docker-compose.frontend.yml` - Next.js
- `docker-compose.twitter-scraper.yml` - Playwright scraper
- `docker-compose.yml` - includes all of the above for a full-stack run

Files that depend on another service `include:` it, so starting any one
file brings up everything it needs and nothing it doesn't.

