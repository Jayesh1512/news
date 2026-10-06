# X Topic Scraper Status

- Input: `TWITTER_SEARCH_QUERY` from runtime configuration.
- Discovery: `twitter search <query> --type <type> --json`.
- Threads: `twitter tweet <matched_id> --json`.
- Persistence: FastAPI `/api/twitter/ingest` into `data/news.json`.
- Deduplication: `tweet_id` for matches, `reply_id` for replies.
- Authentication: `TWITTER_AUTH_TOKEN` and `TWITTER_CT0`.
- Browser dependency: none.

The scraper stores replies from all conversation participants. It does not
limit results to a company profile or to self-replies by the matched author.
