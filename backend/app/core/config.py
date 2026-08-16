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
    cors_origins: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Database
    database_url: str = "postgresql://newsuser:newspass@localhost:5432/newsdb"

    # Supabase (used to store scraped Twitter/X posts)
    supabase_url: str = ""
    supabase_key: str = ""  # service_role key (needed for server-side writes)
    supabase_twitter_table: str = "twitter_posts"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

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
