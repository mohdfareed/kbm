"""Application configuration."""

__all__ = [
    "APP_NAME",
    "CONFIG_FILES",
    "DESCRIPTION",
    "VERSION",
    "ChatHistoryConfig",
    "ConfigFormat",
    "Engine",
    "RAGAnythingConfig",
    "Settings",
    "get_settings",
    "init_settings",
    "reset_settings",
]

import json
from enum import Enum
from importlib.metadata import metadata, version
from pathlib import Path

import typer
import yaml
from pydantic import BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.helpers import error, find_file, settings_to_env

APP_NAME = "kbm"
VERSION = version(APP_NAME)
DESCRIPTION = metadata(APP_NAME)["Summary"]


# MARK: Enums


# Config file names in priority order
CONFIG_FILES = [
    ".env",
    f".{APP_NAME}",
    f".{APP_NAME}.env",
    f".{APP_NAME}.json",
    f".{APP_NAME}.yaml",
    f".{APP_NAME}.yml",
]


class Engine(str, Enum):
    """Available storage engines."""

    CHAT_HISTORY = "chat-history"
    RAG_ANYTHING = "rag-anything"


class ConfigFormat(str, Enum):
    """Config file output formats."""

    JSON = "json"
    YAML = "yaml"
    ENV = "env"

    @property
    def filename(self) -> str:
        """Default config filename for this format."""
        match self:
            case ConfigFormat.JSON:
                return f".{APP_NAME}.json"
            case ConfigFormat.YAML:
                return f".{APP_NAME}.yaml"
            case ConfigFormat.ENV:
                return f".{APP_NAME}.env"

    def dumps(self, data: dict) -> str:
        """Serialize data to string in this format."""
        match self:
            case ConfigFormat.JSON:
                return json.dumps(data, indent=2)
            case ConfigFormat.YAML:
                return yaml.safe_dump(data, sort_keys=False).rstrip()
            case ConfigFormat.ENV:
                return "\n".join(settings_to_env(data, APP_NAME))

    def write(self, path: "Path", data: dict) -> None:
        """Write data to file in this format."""
        content = self.dumps(data)
        if not content.endswith("\n"):
            content += "\n"
        path.write_text(content)


# MARK: Engine Configs


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

    # Query settings
    query_mode: str = "hybrid"  # hybrid, local, global, naive, mix

    # Processing toggles
    enable_image_processing: bool = True
    enable_table_processing: bool = True
    enable_equation_processing: bool = True


# MARK: App Settings


# Default server instructions
DEFAULT_INSTRUCTIONS = """\
You have access to the user's knowledge base - a persistent memory that spans \
conversations, tools, and time. Query it to recall context from previous \
sessions, and insert information worth preserving for future conversations. \
Treat it as shared memory: any model the user talks to can access it, so \
store things in a way that would be useful to a fresh model with no prior context.
"""


class Settings(BaseSettings):
    """Application settings.

    Priority (highest to lowest): CLI args > env vars > config file > defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix=f"{APP_NAME.upper()}_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application settings
    config_file: Path | None = None
    data_dir: Path = Path(typer.get_app_dir(APP_NAME))
    engine: Engine = Engine.CHAT_HISTORY

    # HTTP transport settings
    http_host: str = "127.0.0.1"
    http_port: int = 8000

    # Engine-specific configuration
    chat_history: ChatHistoryConfig = ChatHistoryConfig()
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()

    # Server configuration (user-customizable)
    server_name: str = "memories"
    instructions: str = DEFAULT_INSTRUCTIONS.strip()

    # MARK: Miscellaneous

    @property
    def engine_data_dir(self) -> Path:
        """Resolved data directory for the current engine (not serialized)."""
        match self.engine:
            case Engine.CHAT_HISTORY:
                rel_path = self.chat_history.data_dir
            case Engine.RAG_ANYTHING:
                rel_path = self.rag_anything.data_dir
            case _:
                error(f"Unknown engine: {self.engine}")

        path = Path(rel_path)
        return path if path.is_absolute() else self.data_dir / path

    @model_validator(mode="after")
    def _ensure_directories(self) -> "Settings":
        """Create required directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.engine_data_dir.mkdir(parents=True, exist_ok=True)
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources.

        Priority (highest to lowest): init args > env vars > config file.
        """
        from pydantic_settings import (
            DotEnvSettingsSource,
            JsonConfigSettingsSource,
            YamlConfigSettingsSource,
        )

        sources: list[PydanticBaseSettingsSource] = [init_settings, env_settings]

        # Find config file (searches up directory tree)
        config_file = _pending_config_file or find_file(CONFIG_FILES)

        if config_file:
            suffix = config_file.suffix.lower()
            match suffix:
                case ".yaml" | ".yml":
                    sources.append(YamlConfigSettingsSource(settings_cls, config_file))
                case ".json":
                    sources.append(JsonConfigSettingsSource(settings_cls, config_file))
                case _:
                    # Treat as dotenv (.env, .kbm, etc.)
                    sources.append(DotEnvSettingsSource(settings_cls, config_file))

        return tuple(sources)


# MARK: Settings Management

_settings: Settings | None = None
_pending_config_file: Path | None = None


def get_settings() -> Settings:
    """Get the current settings singleton."""
    if _settings is None:
        raise RuntimeError("Settings not initialized. Call init_settings() first.")
    return _settings


def init_settings(config_path: Path | None = None) -> Settings:
    """Initialize settings with optional config file override."""
    global _settings, _pending_config_file

    # Store config path for settings_customise_sources to use
    _pending_config_file = config_path.resolve() if config_path else None

    # Create settings (triggers settings_customise_sources)
    _settings = Settings()

    # Store which config file was actually used
    config_file = _pending_config_file or find_file(CONFIG_FILES)
    if config_file:
        _settings.config_file = config_file

    _pending_config_file = None
    return _settings


def reset_settings(settings: Settings | None = None) -> None:
    """Reset or replace the settings singleton (for testing)."""
    global _settings
    _settings = settings
