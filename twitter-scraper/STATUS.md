# Twitter Scraper - Current Status

## ✅ Rebuilt on twitter-cli (2026-08-16)

The previous Playwright/Chromium-based scraper was replaced with one built
on [`twitter-cli`](https://github.com/jackwener/twitter-cli) - the same
backend [Agent-Reach](https://github.com/Panniantong/Agent-Reach) uses for
Twitter/X. This removes the ARM64 Playwright build issues entirely (see
[`../STATUS.md`](../STATUS.md) for that history) since there's no browser
in the container at all.

```bash
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

## Summary

- **Base image**: `python:3.12-slim` - no Chromium, no `playwright
  install-deps`, works identically on ARM64 and x86_64.
- **Backend**: `twitter-cli` talks directly to X's internal GraphQL API
  using cookie auth (`TWITTER_AUTH_TOKEN` / `TWITTER_CT0`).
- **Auth is required**: X does not allow meaningful anonymous scraping.
  Set `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` in a repo-root `.env` file
  (see `twitter-scraper/README.md` for how to export these with
  Cookie-Editor). Use a throwaway account, not your main one.
- **Input**: a comma-separated list of profile URLs (or bare handles) via
  `TWITTER_PROFILE_URLS`.
