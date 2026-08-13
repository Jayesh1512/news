from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.article import Source
from app.schemas.article import SourceResponse

router = APIRouter(tags=["sources"])


@router.get("/", response_model=List[SourceResponse])
async def get_sources(db: Session = Depends(get_db)):
    """Get all configured sources."""
    sources = db.query(Source).all()
    return sources


@router.get("/active", response_model=List[SourceResponse])
async def get_active_sources(db: Session = Depends(get_db)):
    """Get only active sources."""
    sources = db.query(Source).filter(Source.is_active == 1).all()
    return sources
