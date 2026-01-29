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

import typer
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.helpers import find_file

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]

# Default data directory (platform-appropriate)
DEFAULT_DATA_DIR = Path(typer.get_app_dir(APP_NAME))

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

    data_dir: str = "chat-history"


class RAGAnythingConfig(BaseModel):
    """RAG-Anything engine settings."""

    data_dir: str = "rag-anything"

    # API settings (defaults to OpenAI-compatible, uses env vars)
    api_key: str | None = None
    base_url: str | None = None

    # Model settings
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 3072

    # Processing toggles
    enable_image_processing: bool = True
    enable_table_processing: bool = True
    enable_equation_processing: bool = True


class Settings(BaseSettings):
    """Application settings."""

    model_config = _model_config

    # Metadata
    config_file: Path | None = _config_file

    # Application settings
    server_name: str = APP_NAME
    data_dir: Path = DEFAULT_DATA_DIR
    engine: Literal["chat-history", "rag-anything"] = "chat-history"

    # Engine-specific configs
    chat_history: ChatHistoryConfig = ChatHistoryConfig()
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()

    @model_validator(mode="after")
    def ensure_data_dir(self) -> "Settings":
        """Create app data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self

    def resolve_data_path(self, path: str) -> Path:
        """Resolve a data path (relative to app data_dir, or absolute)."""
        p = Path(path)
        return p if p.is_absolute() else self.data_dir / p


settings = Settings()
