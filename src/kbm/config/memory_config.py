"""Memory configuration."""

from enum import Enum
from pathlib import Path

from pydantic import computed_field

from .app_config import AppConfig
from .app_settings import app_settings
from .engine_config import (
    CanonicalConfig,
    ChatHistoryConfig,
    Engine,
    FederationConfig,
    RAGAnythingConfig,
)


class Transport(str, Enum):
    """Available transport mechanisms."""

    STDIO = "stdio"
    HTTP = "http"


class MemoryConfig(AppConfig):
    """The configuration for a knowledge base memory."""

    name: str
    engine: Engine = Engine.CHAT_HISTORY
    server_name: str = "memories"
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
    canonical: CanonicalConfig = CanonicalConfig()
    federation: FederationConfig = FederationConfig()

    # MARK: Computed Properties

    @computed_field
    @property
    def is_global(self) -> bool:
        return self.file_path.parent == app_settings.memories_path

    @computed_field
    @property
    def data_path(self) -> Path:
        return app_settings.data_root / self.name

    @computed_field
    @property
    def engine_data_path(self) -> Path:
        return self.data_path / self.engine.value

    @computed_field
    @property
    def canonical_url(self) -> str:
        """Database URL for canonical storage."""
        if self.canonical.database_url:
            return self.canonical.database_url
        db_path = self.data_path / "canonical.db"
        return f"sqlite+aiosqlite:///{db_path}"

    # MARK: Name Resolution

    @classmethod
    def from_name(cls, name: str | None) -> "MemoryConfig":
        if name is None:
            local_files = app_settings.local_config_files()
            if len(local_files) == 1:
                return cls.from_config(local_files[0])

            raise FileNotFoundError(
                "No memory specified and no unique local memory found."
            )

        for config in app_settings.local_config_files():
            cfg = cls.from_config(config)
            if cfg.name == name:
                return cfg

        for config in app_settings.global_config_files():
            cfg = cls.from_config(config)
            if cfg.name == name:
                return cfg

        raise FileNotFoundError(f"Memory not found: {name}")
