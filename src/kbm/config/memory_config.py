"""Memory configuration."""

from enum import Enum
from pathlib import Path

from pydantic import computed_field

from .app_settings import app_settings
from .auth_config import AuthProvider, GithubAuthConfig
from .base_config import NamedFileConfig
from .engine_config import Engine, RAGAnythingConfig


class Transport(str, Enum):
    """Available transport mechanisms."""

    STDIO = "stdio"
    HTTP = "http"


class MemoryConfig(NamedFileConfig):
    """The configuration for a knowledge base memory."""

    # memory settings
    name: str
    instructions: str = (
        "You have access to this project's knowledge base - a persistent memory "
        "that spans conversations, tools, and time. Query it to recall context "
        "from previous sessions, and insert information worth preserving for "
        "future conversations."
    )

    # server settings
    transport: Transport = Transport.STDIO
    host: str = "0.0.0.0"
    port: int = 8000

    # engine settings
    engine: Engine = Engine.CHAT_HISTORY
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()

    # authentication settings
    auth: AuthProvider = AuthProvider.NONE
    github_auth: GithubAuthConfig = GithubAuthConfig()

    # MARK: Computed Properties

    @computed_field
    @property
    def data_path(self) -> Path:
        """Root directory for this memory's data."""
        path = app_settings.data_root / self.name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def log_file(self) -> Path:
        """Path to log file. Parent directory is ensured by app_settings.logs_path."""
        return app_settings.logs_path / f"{self.name}.log"

    @computed_field
    @property
    def engine_data_path(self) -> Path:
        """Directory for engine-specific data."""
        return self.data_path / self.engine.value  # Created by engine if needed

    @computed_field
    @property
    def attachments_path(self) -> Path:
        """Directory for file attachments (inside data_path)."""
        path = self.data_path / "attachments"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def database_url(self) -> str:
        """Database URL for canonical storage."""
        return f"sqlite+aiosqlite:///{self.data_path / 'store.db'}"
