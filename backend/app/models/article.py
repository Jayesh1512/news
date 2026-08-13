from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.db.session import Base


class Article(Base):
    """Article model for storing news articles."""
    
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)  # twitter, reddit, rss, etc.
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    category = Column(String(50), nullable=True, index=True)
    image_url = Column(String(1000), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_source_published', 'source', 'published_at'),
        Index('idx_category_published', 'category', 'published_at'),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}', source='{self.source}')>"


class Source(Base):
    """Source model for tracking scraping sources."""
    
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    platform = Column(String(50), nullable=False)  # twitter, reddit, rss
    url = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1)  # SQLite compatible boolean
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Source(name='{self.name}', platform='{self.platform}')>"
