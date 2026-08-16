# System Status

## Working Components ✅

- **RSS Scraper**: Fully operational, actively scraping articles
- **PostgreSQL Database**: Running and storing articles
- **Redis**: Running on port 6380
- **FastAPI Backend**: Serving at http://localhost:8001
- **Next.js Frontend**: Serving at http://localhost:3001
- **Celery Workers**: Processing scheduled tasks
- **Twitter Scraper**: Rebuilt on Agent-Reach (2026-08-16, see below)

## Twitter Scraper - Rebuilt on Agent-Reach (2026-08-16)

**History**: the original scraper used Playwright/Chromium and failed to
build on ARM64 (`playwright install-deps chromium` on `python:3.11-slim`
tried to apt-install font packages that don't exist under those names on
Debian Trixie). A follow-up fix switched to Microsoft's official Playwright
image and got it building/running, but anonymous browser scraping remained
rate-limited by X. It was then rebuilt around `twitter-cli` directly, then
finally rebuilt again to install and use the actual
[Agent-Reach](https://github.com/Panniantong/Agent-Reach) project (per
explicit request), so the container tracks upstream's chosen Twitter backend
instead of hardcoding one.

**Current approach**: the image installs Agent-Reach from its GitHub source
via `pipx` (Agent-Reach is *not* the "agent-reach" package on PyPI - that's
an unrelated project) and runs its own installer,
`agent-reach install --channels=twitter`, which currently provisions
`twitter-cli`. No browser at all - `twitter-cli` talks directly to X's
internal GraphQL API via cookie auth (`TWITTER_AUTH_TOKEN` / `TWITTER_CT0`).
On startup the scraper logs `agent-reach doctor`'s Twitter channel status
before scraping.

Given a list of profile URLs in `TWITTER_PROFILE_URLS`, it runs
`twitter user-posts <handle> --json` per profile and posts the most recent
tweets to the backend. **Auth is required** - X does not allow meaningful
anonymous access. See `twitter-scraper/README.md` for how to export
`TWITTER_AUTH_TOKEN`/`TWITTER_CT0` from a logged-in session (use a throwaway
account, not your main one).

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

