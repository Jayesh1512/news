from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.constants import TWITTER_ACCOUNTS
from app.scrapers.rss import RSSFeedScraper
from app.scrapers.twitter import TwitterScraper, AUTH_ERROR_CODES
from app.db.session import SessionLocal
from app.db.supabase_client import get_supabase_client, is_supabase_configured
from app.models.article import Article, Source
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
import time

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
)


@celery_app.task(name="scrape_rss_feeds")
def scrape_rss_feeds():
    """Scrape RSS feeds and store articles."""
    import asyncio
    
    async def _scrape():
        scraper = RSSFeedScraper()
        articles = await scraper.scrape(limit=settings.max_articles_per_source)
        
        db = SessionLocal()
        try:
            saved_count = 0
            for article_data in articles:
                # Check if article exists
                existing = db.query(Article).filter(
                    Article.url == article_data["url"]
                ).first()
                
                if not existing:
                    article = Article(**article_data)
                    db.add(article)
                    saved_count += 1
            
            db.commit()
            
            # Update source last_scraped_at
            source = db.query(Source).filter(Source.name == "rss").first()
            if source:
                source.last_scraped_at = datetime.utcnow()
                db.commit()
            
            return {"status": "success", "saved": saved_count, "total": len(articles)}
        
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
        
        finally:
            db.close()
    
    return asyncio.run(_scrape())


@celery_app.task(name="scrape_twitter_accounts")
def scrape_twitter_accounts():
    """Fetch recent posts for each account in TWITTER_ACCOUNTS and upsert
    them into Supabase. Runs every SCRAPE_TWITTER_INTERVAL_HOURS (default
    6h, see celery beat schedule below and app.core.config.Settings).
    """
    if not TWITTER_ACCOUNTS:
        return {"status": "skipped", "message": "No accounts configured in app.core.constants.TWITTER_ACCOUNTS"}

    if not is_supabase_configured():
        return {
            "status": "skipped",
            "message": "Supabase not configured. Set SUPABASE_URL / SUPABASE_KEY (see backend/.env.example).",
        }

    scraper = TwitterScraper()
    if not scraper.is_configured():
        return {
            "status": "skipped",
            "message": "Twitter not configured. Set TWITTER_AUTH_TOKEN / TWITTER_CT0 (see backend/.env.example).",
        }

    supabase = get_supabase_client()
    table = settings.supabase_twitter_table

    total_fetched = 0
    total_upserted = 0
    total_dropped_stale = 0
    auth_failures = 0
    per_account: dict[str, dict] = {}
    max_age_hours = settings.scrape_twitter_interval_hours

    for i, account in enumerate(TWITTER_ACCOUNTS):
        tweets, error_code = scraper.fetch_account_posts(account, settings.twitter_posts_per_account)

        if error_code in AUTH_ERROR_CODES:
            auth_failures += 1

        records = []
        dropped_stale = 0
        for tweet in tweets:
            record = TwitterScraper.tweet_to_record(tweet, account, max_age_hours=max_age_hours)
            if record:
                records.append(record)
            else:
                dropped_stale += 1

        upserted = 0
        if records:
            try:
                supabase.table(table).upsert(records, on_conflict="tweet_id").execute()
                upserted = len(records)
            except Exception as exc:
                logger.error("Supabase upsert failed for @%s: %s", account, exc)
                per_account[account] = {"fetched": len(tweets), "upserted": 0, "dropped_stale": dropped_stale, "error": str(exc)}
                continue

        per_account[account] = {
            "fetched": len(tweets),
            "upserted": upserted,
            "dropped_stale": dropped_stale,
            "error_code": error_code,
        }
        total_fetched += len(tweets)
        total_upserted += upserted
        total_dropped_stale += dropped_stale

        # Small delay between accounts to be gentle on X's rate limits.
        if i < len(TWITTER_ACCOUNTS) - 1:
            time.sleep(5)

    fully_auth_failed = auth_failures == len(TWITTER_ACCOUNTS)
    if fully_auth_failed:
        logger.error(
            "scrape_twitter_accounts: every account (%d/%d) failed with an "
            "auth error. TWITTER_AUTH_TOKEN/TWITTER_CT0 likely expired - "
            "re-export from Cookie-Editor and update .env.",
            auth_failures,
            len(TWITTER_ACCOUNTS),
        )

    return {
        "status": "auth_failed" if fully_auth_failed else "success",
        "accounts": len(TWITTER_ACCOUNTS),
        "max_age_hours": max_age_hours,
        "total_fetched": total_fetched,
        "total_upserted": total_upserted,
        "total_dropped_stale": total_dropped_stale,
        "per_account": per_account,
    }


@celery_app.task(name="scrape_twitter")
def scrape_twitter():
    """Deprecated alias for scrape_twitter_accounts, kept so any external
    callers/queued tasks referencing the old task name still resolve."""
    return scrape_twitter_accounts()


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "scrape-rss-every-15min": {
        "task": "scrape_rss_feeds",
        "schedule": crontab(minute="*/15"),
    },
    "scrape-twitter-accounts-every-6h": {
        "task": "scrape_twitter_accounts",
        "schedule": crontab(minute=0, hour=f"*/{settings.scrape_twitter_interval_hours}"),
    },
}
