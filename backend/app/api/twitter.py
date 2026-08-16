"""Twitter posts API - reads from Supabase (app.db.supabase_client), not
the SQLAlchemy session used by /api/news (RSS articles live in Postgres
via SQLAlchemy; Twitter posts live in Supabase via its REST API/client -
see app/tasks/scrape.py and backend/README.md for why).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.core.config import settings
from app.db.supabase_client import get_supabase_client, is_supabase_configured, SupabaseNotConfiguredError
from app.schemas.article import TwitterPostResponse

router = APIRouter(tags=["twitter"])


@router.get("/", response_model=List[TwitterPostResponse])
async def get_twitter_posts(
    account: Optional[str] = Query(None, description="Filter by source account"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get scraped Twitter/X posts, newest first."""
    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured for this backend.")

    try:
        client = get_supabase_client()
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    query = client.table(settings.supabase_twitter_table).select("*")
    if account:
        query = query.eq("account", account)

    query = query.order("published_at", desc=True).range(offset, offset + limit - 1)

    try:
        result = query.execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {exc}")

    return result.data or []
