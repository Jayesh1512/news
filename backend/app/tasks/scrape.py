from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.scrapers.rss import RSSFeedScraper
from app.scrapers.twitter import TwitterScraper
from app.db.session import SessionLocal
from app.models.article import Article, Source
from sqlalchemy.exc import IntegrityError
from datetime import datetime

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


@celery_app.task(name="scrape_twitter")
def scrape_twitter():
    """Scrape Twitter and store tweets."""
    import asyncio
    
    async def _scrape():
        scraper = TwitterScraper()
        articles = await scraper.scrape(query="technology OR news", limit=settings.max_articles_per_source)
        
        if not articles:
            return {"status": "skipped", "message": "Twitter not configured"}
        
        db = SessionLocal()
        try:
            saved_count = 0
            for article_data in articles:
                existing = db.query(Article).filter(
                    Article.url == article_data["url"]
                ).first()
                
                if not existing:
                    article = Article(**article_data)
                    db.add(article)
                    saved_count += 1
            
            db.commit()
            
            # Update source
            source = db.query(Source).filter(Source.name == "twitter").first()
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


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "scrape-rss-every-15min": {
        "task": "scrape_rss_feeds",
        "schedule": crontab(minute="*/15"),
    },
    "scrape-twitter-every-30min": {
        "task": "scrape_twitter",
        "schedule": crontab(minute="*/30"),
    },
}
