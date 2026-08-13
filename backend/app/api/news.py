from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.article import Article
from app.schemas.article import ArticleResponse, ArticleCreate
from datetime import datetime, timedelta

router = APIRouter(tags=["news"])


@router.get("/", response_model=List[ArticleResponse])
async def get_news(
    source: Optional[str] = Query(None, description="Filter by source (twitter, rss, reddit)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    hours: int = Query(24, ge=1, le=168, description="Articles from last N hours"),
    db: Session = Depends(get_db),
):
    """Get news articles with optional filtering."""
    query = db.query(Article)
    
    # Filter by time
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Article.fetched_at >= cutoff_time)
    
    # Filter by source
    if source:
        query = query.filter(Article.source == source)
    
    # Filter by category
    if category:
        query = query.filter(Article.category == category)
    
    # Order by published_at (newest first), then fetched_at
    query = query.order_by(
        Article.published_at.desc().nullslast(),
        Article.fetched_at.desc()
    )
    
    # Pagination
    articles = query.offset(offset).limit(limit).all()
    
    return articles


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get statistics about the news database."""
    total_articles = db.query(Article).count()
    
    # Articles by source
    from sqlalchemy import func
    by_source = db.query(
        Article.source,
        func.count(Article.id).label('count')
    ).group_by(Article.source).all()
    
    # Articles from last 24 hours
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_count = db.query(Article).filter(
        Article.fetched_at >= recent_cutoff
    ).count()
    
    return {
        "total_articles": total_articles,
        "recent_24h": recent_count,
        "by_source": {source: count for source, count in by_source},
    }


@router.get("/search")
async def search_news(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search news articles by title or content."""
    search_term = f"%{q}%"
    articles = db.query(Article).filter(
        (Article.title.ilike(search_term)) |
        (Article.content.ilike(search_term))
    ).order_by(Article.fetched_at.desc()).limit(limit).all()
    
    return articles


@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
):
    """Create a new article (for internal use / manual testing)."""
    # Check if article with same URL already exists
    existing = db.query(Article).filter(Article.url == article.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Article with this URL already exists")
    
    db_article = Article(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article
