"""Application settings and global computed properties."""

import logging
from importlib.metadata import metadata
from pathlib import Path
from typing import ClassVar

import typer
from pydantic import computed_field

from .base_config import BaseConfig

_meta = metadata("kbm")


class AppSettings(BaseConfig):
    name: ClassVar[str] = _meta["Name"]
    version: ClassVar[str] = _meta["Version"]
    description: ClassVar[str] = _meta["Summary"]

    debug: bool = False
    logger: ClassVar[logging.Logger] = logging.getLogger(name + ".config")
    home: Path = Path(typer.get_app_dir(name))

    @computed_field
    @property
    def logs_path(self) -> Path:
        """Root directory for memory logs storage."""
        return self.home / "logs"

    @computed_field
    @property
    def data_root(self) -> Path:
        """Root directory for memory data storage."""
        return self.home / "data"

    @computed_field
    @property
    def memories_path(self) -> Path:
        """Directory for managed memory config files."""
        return self.home / "memories"

    @property
    def data(self) -> list[Path]:
        """List of available memory data directories."""
        return sorted([f for f in self.data_root.iterdir() if f.is_dir()])

    @property
    def memories(self) -> list[Path]:
        """List of available memory config files."""
        return sorted([f for f in self.memories_path.iterdir() if f.is_file()])

    def ensure_dirs(self) -> None:
        """Create all application directories. Call once during startup."""
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.memories_path.mkdir(parents=True, exist_ok=True)


app_settings = AppSettings()
"""Application settings singleton."""
