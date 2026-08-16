"""Supabase client for storing scraped Twitter/X posts.

Separate from app.db.session (SQLAlchemy/Postgres, used for RSS articles):
Twitter posts go to Supabase instead, per project requirements. Uses a
lazily-created singleton client so importing this module doesn't fail when
Supabase isn't configured (e.g. running only the RSS scraper).
"""
from functools import lru_cache

from app.core.config import settings


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when SUPABASE_URL/SUPABASE_KEY are missing but a Supabase
    operation was attempted."""


@lru_cache(maxsize=1)
def get_supabase_client():
    """Return a cached Supabase client, or raise if not configured."""
    if not settings.supabase_url or not settings.supabase_key:
        raise SupabaseNotConfiguredError(
            "SUPABASE_URL / SUPABASE_KEY are not set. Configure them in .env "
            "(see backend/.env.example) to enable Twitter post storage."
        )

    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_key)


def is_supabase_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_key)
