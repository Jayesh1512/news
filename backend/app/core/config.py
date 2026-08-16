from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Settings
    api_title: str = "News Aggregator API"
    api_version: str = "0.1.0"
    debug: bool = False
    
    # CORS
    cors_origins: str = "http://localhost:8502"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Database - Supabase Postgres connection string, no local Postgres.
    # Empty by default; must be set in .env (see backend/.env.example) or
    # RSS article storage (app/db/session.py) won't be able to connect.
    database_url: str = ""

    # Supabase client (used to store scraped Twitter/X posts via
    # supabase-py / REST API, separate from database_url above which is a
    # direct Postgres connection used by SQLAlchemy)
    supabase_url: str = ""
    supabase_key: str = ""  # service_role key (needed for server-side writes)
    supabase_twitter_table: str = "twitter_posts"

    # Redis
    redis_url: str = "redis://localhost:8500/0"

    # Twitter
    twitter_auth_token: str = ""
    twitter_ct0: str = ""
    twitter_posts_per_account: int = 5
    twitter_cli_timeout_seconds: int = 60

    # Scraping
    scrape_interval_minutes: int = 15
    scrape_twitter_interval_hours: int = 6
    max_articles_per_source: int = 50


settings = Settings()
