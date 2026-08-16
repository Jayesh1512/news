# Twitter Scraper Service

Given a list of X/Twitter **profile URLs**, fetches each profile's most
recent posts and saves them to the backend. Built on
[`twitter-cli`](https://github.com/jackwener/twitter-cli) — the same tool
[Agent-Reach](https://github.com/Panniantong/Agent-Reach) uses as its
Twitter/X backend. No browser, no Playwright/Chromium: it talks straight to
X's internal API using cookie auth.

## Features
- Input is a plain list of profile URLs (or bare `@handles`)
- Fetches each profile's most recent posts via `twitter user-posts <handle> --json`
- Normalizes and POSTs new posts to the backend `/api/news/` endpoint
- Periodic scraping (configurable interval), dedupes against the backend by URL
- Lightweight image: no headless browser, ~150MB

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

## Authentication (required)

X no longer allows meaningful anonymous access, so `twitter-cli` needs
cookie auth. Set `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` from a logged-in
`x.com` session:

1. Log into x.com in a browser, using a **throwaway/secondary account**
   (automated cookie-based access can get flagged - don't use your main
   account).
2. Install the [Cookie-Editor](https://cookie-editor.com/) extension.
3. On x.com, open Cookie-Editor and copy the values of the `auth_token` and
   `ct0` cookies.
4. Put them in a `.env` file at the repo root (picked up automatically by
   `docker compose`):
   ```bash
   TWITTER_AUTH_TOKEN=your_auth_token_value
   TWITTER_CT0=your_ct0_value
   ```
5. Restart the container: `docker compose -f docker-compose.twitter-scraper.yml up -d --build`

Cookies expire periodically (typically weeks) - re-export when the scraper
starts logging auth errors.

## How It Works
1. For each configured profile URL, extracts the `@handle`
2. Runs `twitter user-posts <handle> --max <N> --json` (twitter-cli)
3. Parses the structured JSON output into normalized article records
4. POSTs each to backend `/api/news/` (deduped there by URL)
5. Waits `REQUEST_DELAY` seconds, moves to the next profile
6. Sleeps `SCRAPE_INTERVAL` seconds, repeats

Run a single pass without the loop (useful for testing):

```bash
docker compose -f docker-compose.twitter-scraper.yml run --rm twitter-scraper python -u scraper.py --once
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
- Verify backend is running: `curl http://localhost:8001/health`
- Verify a profile URL resolves to a real handle (typos are skipped with a warning)

**Container crashes / `twitter` command not found:**
- Rebuild: `docker compose -f docker-compose.twitter-scraper.yml build --no-cache twitter-scraper`
