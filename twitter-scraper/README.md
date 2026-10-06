# X Topic Scraper

Searches X for a configurable topic, opens the conversation associated with
each matching post, and sends matching posts plus all fetched replies to the
FastAPI JSON datastore.

Agent-Reach diagnoses the Twitter channel, while the image installs its
selected server backend (`twitter-cli` 0.8.5) directly. Authentication uses
the `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` cookie credentials.

## Configuration

Set these in the repo-root `.env`:

```dotenv
# Normal X search syntax is supported. The topic is never hardcoded.
TWITTER_SEARCH_QUERY="drone delivery" lang:en -filter:retweets
TWITTER_SEARCH_RESULTS=10
TWITTER_SEARCH_TYPE=latest
TWITTER_REPLIES_PER_POST=20
TWITTER_REQUEST_DELAY_SECONDS=2

TWITTER_AUTH_TOKEN=your_auth_token_cookie
TWITTER_CT0=your_ct0_cookie
```

`TWITTER_SEARCH_TYPE` accepts `top`, `latest`, `photos`, or `videos`.

## Run

```bash
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

Run one cycle inside the container:

```bash
docker compose -f docker-compose.twitter-scraper.yml exec twitter-scraper python scraper.py --once
```

This compose file disables the duplicate Celery X task while the standalone
runner is active. RSS scheduling remains enabled.

## Stored records

- `twitter_posts`: each matching post, including its author and
  `search_query`.
- `twitter_replies`: every fetched conversation reply, linked by
  `root_tweet_id`. `is_thread_author` indicates whether the reply came from
  the matched post's author.

Search is retried once because X changes its search GraphQL operation more
often than timeline/thread endpoints. Failures are reported as
`search_failed`; the scraper does not silently fall back to company pages.

Use a secondary X account. Automated cookie access can be rate-limited or
flagged, and search is less stable than direct tweet reads.
