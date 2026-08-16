from pydantic import BaseModel, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional


class ArticleBase(BaseModel):
    """Base schema for article."""
    title: str
    content: Optional[str] = None
    url: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class ArticleCreate(ArticleBase):
    """Schema for creating an article."""
    pass


class ArticleResponse(ArticleBase):
    """Schema for article response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    fetched_at: datetime


class SourceBase(BaseModel):
    """Base schema for source."""
    name: str
    platform: str
    url: Optional[str] = None
    is_active: bool = True


class SourceCreate(SourceBase):
    """Schema for creating a source."""
    pass


class SourceResponse(SourceBase):
    """Schema for source response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    last_scraped_at: Optional[datetime] = None
    created_at: datetime


class TwitterPostResponse(BaseModel):
    """Schema for a scraped Twitter/X post (from Supabase twitter_posts)."""
    model_config = ConfigDict(from_attributes=True)

    tweet_id: str
    account: str
    author: str
    author_name: Optional[str] = None
    text: str
    url: str
    is_retweet: bool = False
    lang: Optional[str] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    media_url: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
