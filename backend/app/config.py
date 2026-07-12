"""
Central configuration. All secrets come from environment variables (.env),
never hard-coded, so the repo is safe to make public on GitHub.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database -----------------------------------------------------
    # Defaults to local SQLite so reviewers can run the project with zero
    # setup. Point DATABASE_URL at Postgres/MySQL in production, e.g.
    #   postgresql+psycopg2://user:pass@localhost:5432/hcp_crm
    #   mysql+pymysql://user:pass@localhost:3306/hcp_crm
    database_url: str = "sqlite:///./hcp_crm.db"

    # --- Groq / LLM -----------------------------------------------------
    groq_api_key: str = ""
    primary_model: str = "llama-3.3-70b-versatile"          # currently supported model
    context_model: str = "llama-3.3-70b-versatile"  # used for heavier reasoning

    # --- App --------------------------------------------------------
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    environment: str = "development"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
