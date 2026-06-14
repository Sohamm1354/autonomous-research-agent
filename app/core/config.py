from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Groq LLM
    groq_api_key:     str
    planner_model:    str = "llama-3.1-8b-instant"
    writer_model:     str = "llama-3.1-8b-instant"
    summariser_model: str = "llama-3.1-8b-instant"

    # Search + scraping
    tavily_api_key:     str
    max_search_results: int = 5
    max_scrape_chars:   int = 6000

    # App
    app_env:      str       = "development"
    log_level:    str       = "INFO"
    cors_origins: list[str] = ["http://localhost:5173",
                               "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra    = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()