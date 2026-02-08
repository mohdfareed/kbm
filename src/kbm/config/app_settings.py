"""Application settings and global computed properties."""

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
    home: Path = Path(typer.get_app_dir(name))

    @computed_field
    @property
    def logs_path(self) -> Path:
        """Root directory for memory logs storage."""
        path = self.home / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def data_root(self) -> Path:
        """Root directory for memory data storage."""
        path = self.home / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def memories_path(self) -> Path:
        """Directory for managed memory config files."""
        path = self.home / "memories"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data(self) -> list[Path]:
        """List of available memory data directories."""
        return sorted([f for f in self.data_root.iterdir() if f.is_dir()])

    @property
    def memories(self) -> list[Path]:
        """List of available memory config files."""
        return sorted([f for f in self.memories_path.iterdir() if f.is_file()])


app_settings = AppSettings()
"""Application settings singleton."""
