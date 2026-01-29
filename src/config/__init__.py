"""Application configuration."""

from enum import Enum
from importlib.metadata import metadata, version

from pydantic_settings import BaseSettings

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]


class EngineType(str, Enum):
    """Available storage engine types."""

    RAG_ANYTHING = "rag-anything"


class Settings(BaseSettings):
    """Application settings."""

    server_name: str = APP_NAME
    engine: EngineType = EngineType.RAG_ANYTHING

    class Config:
        env_prefix = f"{APP_NAME.upper()}_"


settings = Settings()
