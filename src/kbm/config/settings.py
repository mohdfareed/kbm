"""Application settings and global computed properties."""

import logging
from importlib.metadata import metadata
from pathlib import Path
from typing import ClassVar

import typer
from pydantic import PrivateAttr, computed_field

from .base import BaseAppSettings

_meta = metadata("kbm")

# MARK: App Settings
# =============================================================================


class AppSettings(BaseAppSettings):
    name: ClassVar[str] = _meta["Name"]
    version: ClassVar[str] = _meta["Version"]
    description: ClassVar[str] = _meta["Summary"]

    logger: ClassVar[logging.Logger] = logging.getLogger(name + ".config")

    debug: bool = False
    home: Path = Path(typer.get_app_dir(name))
    config_file: Path | None = None

    @computed_field
    @property
    def template_path(self) -> Path:
        """Path to the memory config template file."""
        return self.home / "template.yaml"

    @computed_field
    @property
    def config_path(self) -> Path:
        """Directory for managed memory config files."""
        return self.home / "config"

    @computed_field
    @property
    def logs_path(self) -> Path:
        """Root directory for memory logs storage."""
        return self.home / "logs"

    @computed_field
    @property
    def data_path(self) -> Path:
        """Root directory for memory data storage."""
        return self.home / "data"

    @property
    def memories(self) -> list[Path]:
        """List of all memory config files."""
        if not self.config_path.exists():
            return []

        dirs = [*self.config_path.iterdir(), Path.cwd(), Path.cwd() / ".kbm"]
        return sorted(p for p in dirs if p.suffix in (".yaml", ".yml"))


app_settings = AppSettings()
"""Application settings singleton."""

# MARK: Memory Settings
# =============================================================================


class MemorySettings(BaseAppSettings):
    """The configuration for a knowledge base memory."""

    name: str
    """The unique name/ID of this memory instance."""

    _config_file: Path | None = PrivateAttr(default=None)
    """Override for the config file path (set by factory methods)."""

    @computed_field
    @property
    def config_file(self) -> Path:
        """Path to the memory config file."""
        if self._config_file is not None:
            return self._config_file
        return app_settings.config_path / f"{self.name}.yaml"

    @computed_field
    @property
    def log_file(self) -> Path:
        """Path to log file."""
        return app_settings.logs_path / f"{self.name}.log"

    @computed_field
    @property
    def data_path(self) -> Path:
        """Path to the memory data directory."""
        return app_settings.data_path / self.name

    @computed_field
    @property
    def attachments_path(self) -> Path:
        """Directory for file attachments."""
        return self.data_path / "attachments"

    @computed_field
    @property
    def database_url(self) -> str:
        """Database URL for canonical storage."""
        return f"sqlite+aiosqlite:///{self.data_path / 'store.db'}"

    def ensure_dirs(self) -> None:
        """Ensure memory directories exist."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.attachments_path.mkdir(parents=True, exist_ok=True)
