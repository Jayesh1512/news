from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    async def scrape(self, query: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Scrape articles from the source.
        
        Args:
            query: Search query or topic
            limit: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        pass
    
    def normalize_article(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize scraped data to standard article format.
        
        Args:
            raw_data: Raw article data from scraper
            
        Returns:
            Normalized article dictionary
        """
        return {
            "title": raw_data.get("title", ""),
            "content": raw_data.get("content") or raw_data.get("description", ""),
            "url": raw_data.get("url", ""),
            "source": self.source_name,
            "author": raw_data.get("author"),
            "published_at": self._parse_date(raw_data.get("published_at")),
            "category": raw_data.get("category"),
            "image_url": raw_data.get("image_url"),
        }
    
    def _parse_date(self, date_str: Any) -> datetime | None:
        """Parse date string to datetime object."""
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, str):
            try:
                from dateutil import parser
                return parser.parse(date_str)
            except:
                return None
        return None
