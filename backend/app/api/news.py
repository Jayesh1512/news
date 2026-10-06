from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.db.json_store import DuplicateRecordError, get_json_store
from app.schemas.article import ArticleResponse, ArticleCreate

router = APIRouter(tags=["news"])


@router.get("/", response_model=List[ArticleResponse])
async def get_news(
    source: Optional[str] = Query(None, description="Filter by source (twitter, rss, reddit)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    hours: int = Query(24, ge=1, le=168, description="Articles from last N hours"),
):
    """Get news articles with optional filtering."""
    return get_json_store().list_articles(
        source=source, category=category, limit=limit, offset=offset, hours=hours
    )


@router.get("/stats")
async def get_stats():
    """Get statistics about the JSON datastore."""
    store = get_json_store()
    all_articles = store.list_articles(hours=None, limit=1_000_000)
    recent_articles = store.list_articles(hours=24, limit=1_000_000)
    by_source: dict[str, int] = {}
    for article in all_articles:
        source_name = article.get("source") or "unknown"
        by_source[source_name] = by_source.get(source_name, 0) + 1
    return {
        "total_articles": len(all_articles),
        "recent_24h": len(recent_articles),
        "by_source": by_source,
    }


@router.get("/search")
async def search_news(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search news articles by title or content."""
    return get_json_store().search_articles(q, limit=limit)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    """Get one article by its JSON-assigned numeric id."""
    article = get_json_store().get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    article: ArticleCreate,
):
    """Create a new article (for internal use / manual testing)."""
    try:
        return get_json_store().add_article(article.model_dump())
    except DuplicateRecordError:
        raise HTTPException(status_code=400, detail="Article with this URL already exists")
