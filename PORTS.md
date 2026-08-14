# Port Configuration

Due to conflicts with OrbStack, the default ports have been changed:

## Services

- **Frontend:** http://localhost:3001 (changed from 3000)
- **Backend API:** http://localhost:8001 (changed from 8000)
- **Backend Docs:** http://localhost:8001/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6380 (changed from 6379)

## Twitter Scraper Status

**Currently disabled** due to Docker build complexity with Playwright/Chromium.

The scraper code is complete but requires:
1. Large Playwright base image (~3GB)
2. Complex system dependencies
3. Twitter authentication for production use

**Recommendation:** Use the official Twitter API instead of web scraping for production.

## To Use Default Ports

If you don't have OrbStack or other services using ports 3000, 6379, 8000:

Edit `docker-compose.yml` and change:
- `3001:3000` → `3000:3000`
- `8001:8000` → `8000:8000`
- `6380:6379` → `6379:6379`

Then rebuild: `docker compose up --build`
