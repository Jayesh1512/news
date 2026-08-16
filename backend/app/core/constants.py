"""Constants for the news aggregator backend.

Keep static, rarely-changing lists here rather than scattering them across
config/tasks. Edit TWITTER_ACCOUNTS to change which X/Twitter profiles the
scheduled Twitter scrape job (app.tasks.scrape.scrape_twitter_accounts)
gathers posts from.
"""

# X/Twitter accounts to fetch posts from, every SCRAPE_TWITTER_INTERVAL_HOURS
# (see app.core.config.Settings). Bare handles, no leading "@", no URL.
TWITTER_ACCOUNTS: list[str] = [
    "elonmusk",
    "OpenAI",
    "verge",
    "techcrunch",
    "wired",
]
