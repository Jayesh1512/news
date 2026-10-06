from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


_DEFAULT_DATA_PATH = str(Path(__file__).resolve().parents[3] / "data" / "news.json")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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
    
    # One local datastore shared by the API and scraper processes.
    json_data_path: str = _DEFAULT_DATA_PATH

    # Redis
    redis_url: str = "redis://localhost:8500/0"

    # Twitter
    twitter_auth_token: str = ""
    twitter_ct0: str = ""
    # X search syntax is accepted verbatim, e.g. '"drone delivery" lang:en'.
    # Empty means the scheduled X task is intentionally disabled.
    twitter_search_query: str = ""
    twitter_topic_scraper_enabled: bool = True
    twitter_search_results: int = 10
    twitter_search_type: str = "latest"
    twitter_cli_timeout_seconds: int = 60
    twitter_request_delay_seconds: float = 2.0
    # Max conversation replies to pull per matching search result.
    twitter_replies_per_post: int = 20

    # Profile discovery. Candidate authors come from every stored root post
    # and reply for the topic, then their recent timelines are compared with
    # the topic using local embedding cosine similarity.
    twitter_profile_analysis_after_scrape: bool = False
    twitter_profile_topic: str = ""
    twitter_profile_topic_description: str = ""
    twitter_profile_posts_per_author: int = 15
    twitter_profile_similarity_threshold: float = 0.60
    twitter_profile_embedding_model: str = "text-embedding-3-large"
    twitter_profile_embedding_dimensions: int = 3072
    twitter_profile_summary_model: str = "gpt-6-luna"
    twitter_profile_request_delay_seconds: float = 2.0

    # OpenAI
    openai_api_key: str = ""

    # Scraping
    scrape_interval_minutes: int = 15
    scrape_twitter_interval_hours: int = 6
    max_articles_per_source: int = 50


settings = Settings()
