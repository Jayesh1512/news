# Twitter Scraper Service

Given a list of X/Twitter **profile URLs**, fetches each profile's most
recent posts and saves them to the backend. Built on
[**Agent-Reach**](https://github.com/Panniantong/Agent-Reach) — "give your
AI agent eyes to see the entire internet." Agent-Reach is installed
directly in the image and used to provision and health-check the Twitter
backend (its own `agent-reach install --channels=twitter`), which currently
resolves to [`twitter-cli`](https://github.com/jackwener/twitter-cli). No
browser, no Playwright/Chromium: it talks straight to X's internal API
using cookie auth.

## Why Agent-Reach (not a raw browser scraper)

Agent-Reach is a routing/installer layer: for each platform it picks the
best currently-working backend and re-routes automatically as upstream
tools break or change (its own words: "接入方式会换代，你不用操心" —
backends get swapped out, you don't have to care). This container installs
Agent-Reach itself rather than hardcoding `twitter-cli`, so upgrading
Agent-Reach picks up their latest backend choice for Twitter/X automatically.

**Important:** `pip install agent-reach` on PyPI is an unrelated project.
The real Agent-Reach must be installed from GitHub - this is what the
Dockerfile does (`pipx install https://github.com/Panniantong/agent-reach/archive/main.zip`).

## Features
- Input is a plain list of profile URLs (or bare `@handles`)
- Agent-Reach provisions the Twitter backend at build time
  (`agent-reach install --channels=twitter`)
- On startup, logs `agent-reach doctor`'s Twitter channel status (backend in
  use, credential health) before scraping
- Fetches each profile's most recent posts via `twitter user-posts <handle> --json`
- Normalizes and POSTs new posts to the backend `/api/news/` endpoint
- Periodic scraping (configurable interval), dedupes against the backend by URL

## Configuration

Environment variables set in `../docker-compose.twitter-scraper.yml`:

```yaml
BACKEND_URL: http://backend:8000              # Backend API URL
TWITTER_PROFILE_URLS: https://x.com/user1,https://x.com/user2   # Profile URLs (or bare handles)
POSTS_PER_PROFILE: 10                         # Posts to fetch per profile per run
SCRAPE_INTERVAL: 900                          # Seconds between scrapes (15 min)
REQUEST_DELAY: 5                              # Seconds between profiles (rate limiting)
TWITTER_AUTH_TOKEN: ${TWITTER_AUTH_TOKEN}     # Required - see Authentication below
TWITTER_CT0: ${TWITTER_CT0}                   # Required - see Authentication below
```

## Run standalone

```bash
# From the repo root - also brings up the backend stack this scraper posts to
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

Image build time is longer than a typical Python service (~2 minutes) since
it runs Agent-Reach's own installer, which also sets up `gh` CLI, Node.js,
and `mcporter` as part of its standard install flow.

## Authentication (required)

X no longer allows meaningful anonymous access, so Agent-Reach's Twitter
backend needs cookie auth. Set `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` from a
logged-in `x.com` session:

1. Log into x.com in a browser, using a **throwaway/secondary account**
   (Agent-Reach's own docs recommend this - automated cookie-based access
   can get flagged, don't use your main account).
2. Install the [Cookie-Editor](https://cookie-editor.com/) extension.
3. On x.com, open Cookie-Editor and copy the values of the `auth_token` and
   `ct0` cookies.
4. Put them in a `.env` file at the repo root (picked up automatically by
   `docker compose`):
   ```bash
   TWITTER_AUTH_TOKEN=your_auth_token_value
   TWITTER_CT0=your_ct0_value
   ```
5. Restart: `docker compose -f docker-compose.twitter-scraper.yml up -d --build`

Cookies expire periodically (typically weeks) - re-export when the scraper
starts logging auth errors.

## How It Works
1. At build time, `agent-reach install --channels=twitter` provisions the
   Twitter backend inside the image.
2. At container startup, `agent-reach doctor --json` reports the active
   backend and credential status to the logs.
3. For each configured profile URL, extracts the `@handle`.
4. Runs `twitter user-posts <handle> --max <N> --json` (the backend
   Agent-Reach selected).
5. Parses the structured JSON output into normalized article records.
6. POSTs each to backend `/api/news/` (deduped there by URL).
7. Waits `REQUEST_DELAY` seconds, moves to the next profile.
8. Sleeps `SCRAPE_INTERVAL` seconds, repeats.

Run a single pass without the loop (useful for testing):

```bash
docker compose -f docker-compose.twitter-scraper.yml run --rm twitter-scraper python -u scraper.py --once
```

Check Agent-Reach's own health report directly:

```bash
docker compose -f docker-compose.twitter-scraper.yml run --rm twitter-scraper agent-reach doctor
```

## Rate Limiting
- Configurable delay between profiles (`REQUEST_DELAY`, default 5s)
- Configurable scrape interval (`SCRAPE_INTERVAL`)
- Keep `POSTS_PER_PROFILE` modest (10-20) and the profile list short to
  avoid tripping X's rate limits / account flags

## Troubleshooting

**"No Twitter cookies found" / auth errors in logs:**
- `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` are missing or expired - re-export
  from Cookie-Editor and restart

**No posts saved:**
- Check logs: `docker logs news-twitter-scraper`
- Run `agent-reach doctor` inside the container (see above) to see what
  Agent-Reach thinks is wrong
- Verify backend is running: `curl http://localhost:8001/health`
- Verify a profile URL resolves to a real handle (typos are skipped with a warning)

**Container crashes / `twitter` or `agent-reach` command not found:**
- Rebuild: `docker compose -f docker-compose.twitter-scraper.yml build --no-cache twitter-scraper`
- The build step runs `agent-reach install --channels=twitter`; if that
  step's network calls fail during build (GitHub/PyPI/npm reachability),
  the build itself will fail - check build logs for which step errored.
