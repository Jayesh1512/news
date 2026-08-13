import feedparser
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper
import httpx


class RSSFeedScraper(BaseScraper):
    """Scraper for RSS/Atom feeds."""
    
    def __init__(self, source_name: str = "rss"):
        super().__init__(source_name)
        self.feeds = [
            # Tech news
            "https://news.google.com/rss/search?q=technology&hl=en-US&gl=US&ceid=US:en",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.theverge.com/rss/index.xml",
            # General news
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://www.theguardian.com/world/rss",
        ]
    
    async def scrape(self, query: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Scrape articles from RSS feeds."""
        articles = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for feed_url in self.feeds[:3]:  # Limit to 3 feeds for now
                try:
                    response = await client.get(feed_url)
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries[:limit // 3]:
                        article = self.normalize_article({
                            "title": entry.get("title", ""),
                            "description": entry.get("summary", ""),
                            "url": entry.get("link", ""),
                            "author": entry.get("author"),
                            "published_at": entry.get("published"),
                            "category": "technology" if "tech" in feed_url.lower() else "general",
                        })
                        articles.append(article)
                        
                        if len(articles) >= limit:
                            break
                            
                except Exception as e:
                    print(f"Error scraping feed {feed_url}: {e}")
                    continue
                    
                if len(articles) >= limit:
                    break
        
        return articles[:limit]
