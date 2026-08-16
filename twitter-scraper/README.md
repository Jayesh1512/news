# Twitter Scraper Service

Playwright-based scraper for collecting tweets from specified accounts.

## Features
- Headless Chromium browser with stealth mode
- Scrapes tweets from configured Twitter accounts
- Auto-saves to backend API
- Periodic scraping (configurable interval)
- Anti-detection measures

## Configuration

Environment variables set in `../docker-compose.twitter-scraper.yml`:

```yaml
BACKEND_URL: http://backend:8000          # Backend API URL
TWITTER_ACCOUNTS: user1,user2,user3       # Comma-separated usernames
SCRAPE_INTERVAL: 900                      # Seconds between scrapes (15 min)
```

## Run standalone

```bash
# From the repo root - also brings up the backend stack this scraper posts to
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

## Default Accounts
- @elonmusk
- @OpenAI
- @verge
- @techcrunch
- @wired

## How It Works
1. Launches headless Chromium with stealth techniques
2. Navigates to each account's Twitter profile
3. Scrolls to load recent tweets
4. Extracts: text, timestamp, link, author
5. POSTs to backend `/api/news/` endpoint
6. Waits for next interval

## Authentication
Twitter requires login for full access. To enable authenticated scraping:

1. Add cookies/session to the scraper
2. Or use Twitter API credentials (requires developer account)
3. Or use browser automation with manual login (not recommended for production)

## Rate Limiting
- 5-second delay between accounts
- Configurable scrape interval
- Limits to 10 tweets per account per run

## Troubleshooting

**Scraper can't access tweets:**
- Twitter may block headless browsers
- Enable login/cookies in scraper.py
- Or use official Twitter API instead

**High memory usage:**
- Adjust `shm_size` in docker-compose.yml
- Reduce number of accounts

**Container crashes:**
- Check `docker logs news-twitter-scraper`
- Verify Playwright browser installation
