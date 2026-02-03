"""Memory configuration."""

__all__ = ["MemoryConfig", "Transport"]

from enum import Enum
from pathlib import Path
from typing import ClassVar, cast

import yaml
from pydantic import computed_field
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from kbm.config.app_metadata import app_metadata
from kbm.config.engine_config import (
    ChatHistoryConfig,
    Engine,
    EngineConfig,
    RAGAnythingConfig,
)


class Transport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"


class MemoryConfig(BaseSettings):
    """Memory configuration loaded from YAML + .env + env vars."""

    EXCLUDE_FIELDS: ClassVar[set[str]] = {"file_path"}

    model_config = SettingsConfigDict(
        env_prefix="KBM_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    name: str
    file_path: Path

    engine: Engine = Engine.CHAT_HISTORY
    instructions: str = (
        "You have access to this project's knowledge base - a persistent memory "
        "that spans conversations, tools, and time. Query it to recall context "
        "from previous sessions, and insert information worth preserving for "
        "future conversations."
    )

    transport: Transport = Transport.STDIO
    host: str = "0.0.0.0"
    port: int = 8000

    chat_history: ChatHistoryConfig = ChatHistoryConfig()
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()

    @computed_field
    @property
    def data_path(self) -> Path:
        return app_metadata.data_root / self.name

    @computed_field
    @property
    def engine_data_path(self) -> Path:
        return self.data_path / self.engine.value

    @computed_field
    @property
    def engine_config(self) -> EngineConfig:
        match self.engine:
            case Engine.CHAT_HISTORY:
                return self.chat_history
            case Engine.RAG_ANYTHING:
                return self.rag_anything

    # MARK: Configuration Management

    @classmethod
    def load(cls, name: str | None, config: Path | None) -> "MemoryConfig":
        """Load config from a YAML file."""
        if name and config:
            raise ValueError("Cannot specify both name and config.")

        if config:
            path = config.expanduser().resolve()
        elif name:
            path = app_metadata.named_config_path(name)
        else:
            path = app_metadata.local_config_path()

        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")
        return cls(file_path=path, _yaml_file=path)  # type: ignore[call-arg]

    def dump(self, full: bool = False) -> str:
        """Serialize config to YAML. If full=False, excludes defaults."""
        data = self.model_dump(
            mode="json",  # Serialize enums as their values
            exclude=self.EXCLUDE_FIELDS,
            exclude_computed_fields=True,
            exclude_defaults=not full,
        )
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        init_src = cast(InitSettingsSource, init_settings)
        yaml_file: Path | None = init_src.init_kwargs.get("_yaml_file")
        json_file: Path | None = init_src.init_kwargs.get("_json_file")

        # Priority: init > env > dotenv > config files > secrets
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file),
            JsonConfigSettingsSource(settings_cls, json_file),
            file_secret_settings,
        )
