from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Any, Literal, Optional


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
    """Schema for a scraped Twitter/X post from the JSON datastore."""
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
    search_query: Optional[str] = None
    fetched_at: datetime


class TwitterReplyResponse(BaseModel):
    """Schema for a reply in a conversation matched by X search."""
    model_config = ConfigDict(from_attributes=True)

    reply_id: str
    root_tweet_id: str
    account: str
    author: str
    author_name: Optional[str] = None
    text: str
    url: str
    lang: Optional[str] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    media_url: Optional[str] = None
    published_at: Optional[datetime] = None
    search_query: Optional[str] = None
    is_thread_author: bool = False
    fetched_at: datetime


class TwitterThreadResponse(BaseModel):
    """A topic-search match grouped with its associated conversation."""

    post: TwitterPostResponse
    replies: list[TwitterReplyResponse] = Field(default_factory=list)


class TwitterIngestRequest(BaseModel):
    """Batch produced by the optional standalone Agent-Reach container."""

    posts: list[dict[str, Any]] = Field(default_factory=list)
    replies: list[dict[str, Any]] = Field(default_factory=list)
    analyze_profiles: Optional[bool] = None


class TwitterProfileSourceResponse(BaseModel):
    type: Literal["post", "reply"]
    id: str
    url: Optional[str] = None
    root_tweet_id: Optional[str] = None


class TwitterProfilePostResponse(BaseModel):
    tweet_id: str
    text: str
    url: str
    published_at: Optional[datetime] = None
    lang: Optional[str] = None
    is_retweet: bool = False
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    similarity: float
    matches_topic: bool
    matched_context: Optional[str] = None


class TwitterProfileSummaryResponse(BaseModel):
    overview: str
    topic_connection: str
    primary_topics: list[str] = Field(default_factory=list)
    key_signals: list[str] = Field(default_factory=list)


class TwitterProfileResponse(BaseModel):
    profile_key: str
    topic: str
    topic_description: str
    context_sentences: list[str] = Field(default_factory=list)
    username: str
    display_name: Optional[str] = None
    profile_url: str
    discovered_from: list[TwitterProfileSourceResponse] = Field(default_factory=list)
    analyzed_post_count: int = 0
    matching_post_count: int = 0
    best_similarity: float = 0
    similarity_threshold: float
    embedding_model: str
    summary: Optional[TwitterProfileSummaryResponse] = None
    summary_model: Optional[str] = None
    summary_error: Optional[str] = None
    summary_generated_at: Optional[datetime] = None
    recent_posts: list[TwitterProfilePostResponse] = Field(default_factory=list)
    matching_posts: list[TwitterProfilePostResponse] = Field(default_factory=list)
    fetch_error: Optional[str] = None
    analysis_error: Optional[str] = None
    analyzed_at: datetime


class TwitterProfileAnalysisRequest(BaseModel):
    topic: Optional[str] = None
    topic_description: Optional[str] = None
    context_sentences: list[str] = Field(default_factory=list, max_length=8)
    posts_per_author: Optional[int] = Field(default=None, ge=10, le=15)
    similarity_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    run_mode: Literal["celery", "inline"] = "celery"


class TwitterTopicDiscoveryRequest(BaseModel):
    """A user topic that should be expanded, searched, and analyzed."""

    topic: str = Field(min_length=2, max_length=160)
    search_type: Literal["top", "latest", "photos", "videos"] = "latest"
    search_results: int = Field(default=10, ge=1, le=20)
    replies_per_post: int = Field(default=20, ge=1, le=100)
    posts_per_author: int = Field(default=15, ge=10, le=15)
    similarity_threshold: float = Field(default=0.60, ge=0, le=1)
