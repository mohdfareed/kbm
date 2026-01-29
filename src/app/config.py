"""Application configuration."""

__all__ = [
    "APP_NAME",
    "DESCRIPTION",
    "VERSION",
    "settings",
    "Settings",
    "ChatHistoryConfig",
    "RAGAnythingConfig",
]

from importlib.metadata import metadata, version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.helpers import find_file

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]

# Config file names in priority order
CONFIG_FILES = (".env", "kbm.yaml", "kbm.yml", "kbm.json")

_config_file = find_file(CONFIG_FILES)
_model_config = SettingsConfigDict(
    env_prefix=f"{APP_NAME.upper()}_",
    env_nested_delimiter="__",
    env_file=_config_file
    if _config_file and _config_file.suffix == ".env"
    else None,
    yaml_file=_config_file
    if _config_file and _config_file.suffix in (".yaml", ".yml")
    else None,
    json_file=_config_file
    if _config_file and _config_file.suffix == ".json"
    else None,
    extra="ignore",
)


# MARK: Settings models


class ChatHistoryConfig(BaseModel):
    """Chat history engine settings."""

    data_dir: str = "./data/chat-history"


class RAGAnythingConfig(BaseModel):
    """RAG-Anything engine settings."""

    working_dir: str = "./data"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"


class Settings(BaseSettings):
    """Application settings."""

    model_config = _model_config

    # Metadata
    config_file: Path | None = _config_file

    # Application settings
    server_name: str = APP_NAME
    engine: Literal["chat-history", "rag-anything"] = "chat-history"

    # Engine-specific configs
    chat_history: ChatHistoryConfig = ChatHistoryConfig()
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()


settings = Settings()
