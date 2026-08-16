# 🐦 Twitter Scraper - Setup Complete

## ✅ What's Ready

All Twitter scraper files are in place:
```
twitter-scraper/
├── Dockerfile          # Container definition
├── scraper.py          # Playwright scraping logic (156 lines)
├── requirements.txt    # Python dependencies
├── README.md           # Full usage guide
├── .env.example        # Configuration template
└── CHECKLIST.md        # Pre-launch checklist
```

`docker-compose.yml` includes the service configuration.

## 🚀 When You're Ready to Use It

### 1. Build the container
```bash
docker compose -f docker-compose.twitter-scraper.yml build twitter-scraper
```
**Note:** First build takes ~5-10 minutes (downloads Chromium browser)

### 2. (Optional) Add Twitter credentials
Edit `docker-compose.twitter-scraper.yml`:
```yaml
twitter-scraper:
  environment:
    TWITTER_USERNAME: your_username  # Add this
    TWITTER_PASSWORD: your_password  # Add this
```

### 3. Start it
```bash
docker compose -f docker-compose.twitter-scraper.yml up -d
```

### 4. Verify
```bash
# Watch logs
docker logs -f news-twitter-scraper

# Check for tweets in API
curl http://localhost:8001/api/news/?source=twitter
```

## 📋 Quick Reference

**Default accounts:** @elonmusk, @OpenAI, @verge, @techcrunch, @wired  
**Scrape interval:** Every 15 minutes (900s)  
**Tweets per run:** 10 per account  
**Auto-save:** Posts to backend `/api/news/`

**Change accounts:** Edit `TWITTER_ACCOUNTS` in `docker-compose.twitter-scraper.yml`  
**Change interval:** Edit `SCRAPE_INTERVAL` in `docker-compose.twitter-scraper.yml`

## ⚠️ Important Notes

1. **Twitter may require login** for full access
   - Without auth: limited to public tweets
   - With auth: full access but riskier (account could be flagged)
   - Alternative: Use official Twitter API (requires developer account)

2. **Browser download happens during build**
   - Adds ~500MB to container
   - Only downloads once, cached after that

3. **Memory usage**
   - Chromium: ~300-500MB RAM
   - Total container: ~600-800MB

4. **Rate limiting**
   - 5-second delay between accounts
   - Respect Twitter's limits
   - Increase interval if you hit rate limits

## 🔄 Alternative: Twitter API

For production, consider the official API:
- More reliable
- Better rate limits  
- No browser overhead
- Requires Twitter Developer account (free tier available)
- See [Twitter Developer Portal](https://developer.twitter.com/)

---

**Status:** Container ready to build and run whenever you need it!
