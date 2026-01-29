"""Application configuration."""

from importlib.metadata import metadata, version

from pydantic_settings import BaseSettings

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]


class Settings(BaseSettings):
    """Application settings."""

    server_name: str = APP_NAME

    class Config:
        env_prefix = f"{APP_NAME.upper()}_"


settings = Settings()
