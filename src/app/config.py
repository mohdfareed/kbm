"""Application configuration."""

__all__ = [
    "APP_NAME",
    "CONFIG_FILES",
    "DESCRIPTION",
    "VERSION",
    "ChatHistoryConfig",
    "Engine",
    "Format",
    "RAGAnythingConfig",
    "Settings",
    "get_settings",
    "init_settings",
]

from enum import Enum
from importlib.metadata import metadata, version
from pathlib import Path
from typing import Self

import typer
from pydantic import BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    JsonConfigSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from app.helpers import find_file

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]

# Default data directory (platform-appropriate)
DEFAULT_DATA_DIR = Path(typer.get_app_dir(APP_NAME))

# Config file names by format
CONFIG_FILE_YAML = "kbm.yaml"
CONFIG_FILE_JSON = "kbm.json"
CONFIG_FILE_ENV = ".env"

# Config file names in priority order
CONFIG_FILES = (CONFIG_FILE_ENV, CONFIG_FILE_YAML, "kbm.yml", CONFIG_FILE_JSON)


class Engine(str, Enum):
    """Available storage engines."""

    chat_history = "chat-history"
    rag_anything = "rag-anything"


class Format(str, Enum):
    """Config file output formats."""

    yaml = "yaml"
    json = "json"
    env = "env"

    @property
    def filename(self) -> str:
        """Default config filename for this format."""
        return {
            Format.yaml: CONFIG_FILE_YAML,
            Format.json: CONFIG_FILE_JSON,
            Format.env: CONFIG_FILE_ENV,
        }[self]


# MARK: Engine settings


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


# MARK: App settings


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix=f"{APP_NAME.upper()}_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application settings
    config_file: Path | None = None
    data_dir: Path = DEFAULT_DATA_DIR
    server_name: str = APP_NAME
    engine: Engine = Engine.chat_history

    # Engine-specific configs
    chat_history: ChatHistoryConfig = ChatHistoryConfig()
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()

    # MARK: - Settings methods

    def resolve_data_path(self, path: str) -> Path:
        """Resolve a data path (relative to app data_dir, or absolute)."""
        p = Path(path)
        return p if p.is_absolute() else self.data_dir / p

    @model_validator(mode="after")
    def ensure_data_dir(self) -> "Settings":
        """Create app data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self

    # MARK: - Loading from files

    @classmethod
    def from_yaml(cls, path: Path) -> Self:
        """Load settings from a YAML file."""
        file_settings = YamlConfigSettingsSource(cls, path)()
        return cls(**cls._merge_with_env(file_settings), config_file=path)

    @classmethod
    def from_json(cls, path: Path) -> Self:
        """Load settings from a JSON file."""
        file_settings = JsonConfigSettingsSource(cls, path)()
        return cls(**cls._merge_with_env(file_settings), config_file=path)

    @classmethod
    def from_env(cls, path: Path) -> Self:
        """Load settings from a .env file."""
        file_settings = DotEnvSettingsSource(cls, path)()
        return cls(**cls._merge_with_env(file_settings), config_file=path)

    @classmethod
    def _merge_with_env(cls, file_settings: dict) -> dict:
        """Merge file settings with env vars (env vars take precedence)."""
        env_settings = EnvSettingsSource(cls, case_sensitive=False)()
        return {k: v for k, v in file_settings.items() if k not in env_settings}


# MARK: Settings management

_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the current settings singleton."""
    if _settings is None:
        raise RuntimeError("Settings not initialized. Call init_settings() first.")
    return _settings


def init_settings(config_path: Path | None = None) -> Settings:
    """Initialize settings with optional config file override."""
    global _settings

    # Find config file if not provided
    config_file = config_path.resolve() if config_path else find_file(CONFIG_FILES)

    # Load from file based on type, or default
    if config_file:
        if config_file.suffix in (".yaml", ".yml"):
            _settings = Settings.from_yaml(config_file)
        elif config_file.suffix == ".json":
            _settings = Settings.from_json(config_file)
        elif config_file.suffix.endswith(".env"):
            _settings = Settings.from_env(config_file)
        else:
            _settings = Settings.from_env(config_file)
    else:
        _settings = Settings()

    return _settings
