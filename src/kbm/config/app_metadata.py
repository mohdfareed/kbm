"""Application metadata."""

__all__ = ["app_metadata"]

import os
from functools import cached_property
from importlib.metadata import metadata
from pathlib import Path

import typer
from pydantic import BaseModel

_meta = metadata("kbm")


class _AppMetadata(BaseModel):
    """Application metadata. Singleton instance exported as `app_metadata`."""

    name: str = _meta["Name"]
    version: str = _meta["Version"]
    description: str = _meta["Summary"]

    @cached_property
    def home(self) -> Path:
        """KBM home directory ($KBM_HOME or platform default)."""
        if env := os.environ.get("KBM_HOME"):
            return Path(env).expanduser().resolve()
        return Path(typer.get_app_dir(self.name))

    @cached_property
    def memories_path(self) -> Path:
        """Directory for managed memory config files."""
        return self.home / "memories"

    @cached_property
    def data_root(self) -> Path:
        """Root directory for all memory data ($KBM_HOME/data/)."""
        return self.home / "data"

    def local_config_path(self) -> Path:
        """Path to local config (.kbm.yaml in cwd)."""
        return Path.cwd() / ".kbm.yaml"

    def named_config_path(self, name: str) -> Path:
        """Path to global memory config ($KBM_HOME/memories/{name}.yaml)."""
        return self.memories_path / f"{name}.yaml"


app_metadata = _AppMetadata()
"""Application metadata singleton."""
