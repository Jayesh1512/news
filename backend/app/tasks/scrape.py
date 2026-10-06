from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.scrapers.rss import RSSFeedScraper
from app.scrapers.twitter import TwitterScraper, AUTH_ERROR_CODES
from app.services.twitter_profile_analysis import run_profile_analysis
from app.db.json_store import get_json_store
import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "news_aggregator",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="scrape_rss_feeds")
def scrape_rss_feeds():
    """Scrape RSS feeds and store articles."""
    import asyncio
    
    async def _scrape():
        scraper = RSSFeedScraper()
        articles = await scraper.scrape(limit=settings.max_articles_per_source)
        
        try:
            store = get_json_store()
            saved_count = store.add_articles(articles)
            store.record_source("rss", "rss")
            return {"status": "success", "saved": saved_count, "total": len(articles)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    return asyncio.run(_scrape())


def _run_twitter_topic_scrape(
    *,
    search_query: str,
    topic: str | None = None,
    analyze_profiles: bool = False,
    topic_description: str | None = None,
    context_sentences: list[str] | None = None,
    search_results: int | None = None,
    search_type: str | None = None,
    replies_per_post: int | None = None,
    posts_per_author: int | None = None,
    similarity_threshold: float | None = None,
    progress: Callable[[str, int | None, int | None], None] | None = None,
):
    """Search one arbitrary X query, store it under a topic, then analyze."""
    search_query = search_query.strip()
    topic = (topic or search_query).strip()
    if not search_query:
        return {
            "status": "skipped",
            "message": "No X search query was provided.",
        }
    selected_search_type = search_type or settings.twitter_search_type
    selected_search_results = search_results or settings.twitter_search_results
    selected_replies_per_post = replies_per_post or settings.twitter_replies_per_post

    scraper = TwitterScraper()
    if not scraper.is_configured():
        return {
            "status": "skipped",
            "message": "Twitter not configured. Set TWITTER_AUTH_TOKEN / TWITTER_CT0 (see backend/.env.example).",
        }

    store = get_json_store()

    if progress:
        progress("searching_x", None, None)
    tweets, error_code = scraper.search_posts(
        search_query,
        selected_search_results,
        selected_search_type,
    )
    if error_code:
        status = "auth_failed" if error_code in AUTH_ERROR_CODES else "search_failed"
        return {
            "status": status,
            "topic": topic,
            "search_query": search_query,
            "error_code": error_code,
            "total_fetched": 0,
            "total_upserted": 0,
            "total_replies_fetched": 0,
            "total_replies_upserted": 0,
        }

    records = []
    for tweet in tweets:
        record = TwitterScraper.tweet_to_record(tweet, search_query=topic)
        if record:
            records.append(record)

    posts_upserted = store.upsert_twitter_posts(records)
    reply_records = []
    replies_fetched = 0
    thread_errors: dict[str, str] = {}

    for index, record in enumerate(records):
        if progress:
            progress("fetching_conversations", index + 1, len(records))
        root_tweet_id = record["tweet_id"]
        replies, reply_error_code = scraper.fetch_tweet_replies(
            root_tweet_id, selected_replies_per_post
        )
        if reply_error_code:
            thread_errors[root_tweet_id] = reply_error_code
        else:
            replies_fetched += len(replies)
            for reply in replies:
                reply_record = TwitterScraper.reply_to_record(
                    reply,
                    record["author"],
                    root_tweet_id,
                    search_query=topic,
                )
                if reply_record:
                    reply_records.append(reply_record)
        if index < len(records) - 1:
            time.sleep(settings.twitter_request_delay_seconds)

    replies_upserted = store.upsert_twitter_replies(reply_records)

    result = {
        "status": "success",
        "topic": topic,
        "search_query": search_query,
        "search_type": selected_search_type,
        "total_fetched": len(tweets),
        "total_upserted": posts_upserted,
        "total_replies_fetched": replies_fetched,
        "total_replies_upserted": replies_upserted,
        "thread_errors": thread_errors,
    }
    if analyze_profiles:
        try:
            if progress:
                progress("analyzing_profiles", None, None)
            result["profile_analysis"] = run_profile_analysis(
                topic=topic,
                topic_description=topic_description,
                context_sentences=context_sentences,
                posts_per_author=posts_per_author,
                similarity_threshold=similarity_threshold,
            )
        except Exception as exc:
            logger.exception("Profile analysis failed after X topic scrape")
            result["profile_analysis"] = {
                "status": "error",
                "message": f"{type(exc).__name__}: {exc}",
            }
    return result


@celery_app.task(name="scrape_twitter_topic")
def scrape_twitter_topic(analyze_profiles: bool | None = None):
    """Search X for the configured scheduled topic."""
    if not settings.twitter_topic_scraper_enabled:
        return {"status": "skipped", "message": "Scheduled X topic scraper is disabled."}

    search_query = settings.twitter_search_query.strip()
    if not search_query:
        return {
            "status": "skipped",
            "message": "No X topic configured. Set TWITTER_SEARCH_QUERY.",
        }
    should_analyze = (
        settings.twitter_profile_analysis_after_scrape
        if analyze_profiles is None
        else analyze_profiles
    )
    return _run_twitter_topic_scrape(
        search_query=search_query,
        analyze_profiles=should_analyze,
    )


@celery_app.task(name="discover_twitter_topic", bind=True)
def discover_twitter_topic(
    self,
    *,
    topic: str,
    search_query: str,
    topic_description: str,
    context_sentences: list[str],
    search_type: str = "latest",
    search_results: int = 10,
    replies_per_post: int = 20,
    posts_per_author: int = 15,
    similarity_threshold: float = 0.60,
):
    """Interactive end-to-end topic discovery, independent of the schedule."""

    def report(phase: str, current: int | None, total: int | None) -> None:
        self.update_state(
            state="PROGRESS",
            meta={"phase": phase, "current": current, "total": total},
        )

    return _run_twitter_topic_scrape(
        search_query=search_query,
        topic=topic,
        analyze_profiles=True,
        topic_description=topic_description,
        context_sentences=context_sentences,
        search_type=search_type,
        search_results=search_results,
        replies_per_post=replies_per_post,
        posts_per_author=posts_per_author,
        similarity_threshold=similarity_threshold,
        progress=report,
    )


@celery_app.task(name="analyze_twitter_profiles")
def analyze_twitter_profiles(
    topic: str | None = None,
    topic_description: str | None = None,
    context_sentences: list[str] | None = None,
    posts_per_author: int | None = None,
    similarity_threshold: float | None = None,
):
    """Analyze every unique author already discovered for an X topic."""
    selected_topic = (
        topic or settings.twitter_profile_topic or settings.twitter_search_query
    ).strip()
    if not selected_topic:
        return {
            "status": "skipped",
            "message": "No profile topic configured. Set TWITTER_PROFILE_TOPIC or TWITTER_SEARCH_QUERY.",
        }
    if not settings.openai_api_key:
        return {
            "status": "skipped",
            "message": "OPENAI_API_KEY is required for cosine profile analysis.",
        }
    if not TwitterScraper().is_configured():
        return {
            "status": "skipped",
            "message": "Twitter not configured. Set TWITTER_AUTH_TOKEN / TWITTER_CT0.",
        }
    return run_profile_analysis(
        topic=selected_topic,
        topic_description=topic_description,
        context_sentences=context_sentences,
        posts_per_author=posts_per_author,
        similarity_threshold=similarity_threshold,
    )


@celery_app.task(name="scrape_twitter_accounts")
def scrape_twitter_accounts():
    """Backward-compatible alias for the former account-based task."""
    return scrape_twitter_topic()


@celery_app.task(name="scrape_twitter")
def scrape_twitter():
    """Deprecated alias for scrape_twitter_topic, kept so any external
    callers/queued tasks referencing the old task name still resolve."""
    return scrape_twitter_topic()


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "scrape-rss-every-15min": {
        "task": "scrape_rss_feeds",
        "schedule": crontab(minute="*/15"),
    },
    "scrape-twitter-topic-every-6h": {
        "task": "scrape_twitter_topic",
        "schedule": crontab(minute=0, hour=f"*/{settings.scrape_twitter_interval_hours}"),
    },
}
