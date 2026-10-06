from fastapi import APIRouter
from typing import List
from app.db.json_store import get_json_store
from app.schemas.article import SourceResponse

router = APIRouter(tags=["sources"])


@router.get("/", response_model=List[SourceResponse])
async def get_sources():
    """Get all configured sources."""
    return get_json_store().list_sources()


@router.get("/active", response_model=List[SourceResponse])
async def get_active_sources():
    """Get only active sources."""
    return get_json_store().list_sources(active_only=True)
