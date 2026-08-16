# Twitter Scraper - Current Status

## ✅ Operational

Fixed 2026-08-16. Builds and runs via:

```bash
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

See [`../STATUS.md`](../STATUS.md) for the root-cause writeup and
verification evidence.

## Summary

- **Base image**: `mcr.microsoft.com/playwright/python` (Chromium + OS deps
  preinstalled and version-matched, works the same on ARM64 and x86_64).
- **Auth**: anonymous scraping works but is rate-limited by Twitter/X. Set
  `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` in `.env` for reliable access.
- **Recommendation for production**: consider Twitter API v2 instead of
  browser scraping for better reliability and rate limits.
