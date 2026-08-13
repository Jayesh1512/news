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
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Twitter
    twitter_auth_token: str = ""
    twitter_ct0: str = ""
    
    # Scraping
    scrape_interval_minutes: int = 15
    max_articles_per_source: int = 50


settings = Settings()
