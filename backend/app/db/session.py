"""SQLAlchemy session for RSS articles/sources, stored in Supabase's
Postgres database (DATABASE_URL should be a Supabase connection string -
see backend/.env.example). There is no local Postgres container; Supabase
is the only Postgres this backend talks to.

Twitter posts use a separate path: app.db.supabase_client (the Supabase
Python client / REST API), not this SQLAlchemy session.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
