# News Aggregator - Implementation Summary

## Current architecture

- FastAPI serves news, source, Twitter post, and Twitter reply APIs.
- Celery schedules RSS every 15 minutes and X scraping every 6 hours.
- All persistent records live in one atomic, file-locked document:
  `data/news.json`.
- Next.js 16 reads through FastAPI and caches backend fetches for 60 seconds.
- Redis is used only as the Celery broker/result backend.

## JSON collections

The datastore contains `articles`, `sources`, `twitter_posts`, and
`twitter_replies`. Articles deduplicate by URL; X posts and replies upsert by
`tweet_id` and `reply_id` respectively.

## Verified paths

- FastAPI article creation, duplicate rejection, listing, detail, search, and
  stats.
- FastAPI X post and reply listing.
- Live RSS scrape persisted six articles and one source into temporary JSON.
- The X pipeline stores configurable topic matches and full conversations.
- Next.js lint and production build.
- All Docker Compose entry points validate.

## Run

```bash
docker compose up -d --build
```

The UI is available at http://localhost:8502 and API docs at
http://localhost:8501/docs. X scraping requires `TWITTER_AUTH_TOKEN` and
`TWITTER_CT0` in the repo-root `.env`; RSS and the UI do not.
