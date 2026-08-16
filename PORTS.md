# Port Configuration

Due to conflicts with OrbStack, the default host ports have been changed:

## Services

- **Frontend:** http://localhost:3001 (changed from 3000)
- **Backend API:** http://localhost:8001 (changed from 8000)
- **Backend Docs:** http://localhost:8001/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6380 (changed from 6379)

## Twitter Scraper

Runs on Microsoft's official Playwright image (`mcr.microsoft.com/playwright/python`),
which ships Chromium and its system dependencies pre-installed, so it builds
and runs the same on ARM64 and x86_64. See `twitter-scraper/README.md`.

## To Use Default Ports

If you don't have OrbStack or other services using ports 3000, 6379, 8000,
edit the relevant per-service compose file(s) and change:

- `docker-compose.frontend.yml`: `3001:3000` → `3000:3000`
- `docker-compose.backend.yml`: `8001:8000` → `8000:8000`
- `docker-compose.redis.yml`: `6380:6379` → `6379:6379`

Then rebuild: `docker compose up --build`
