"""Application settings."""

import os
from functools import cached_property
from importlib.metadata import metadata
from pathlib import Path

import dotenv
import typer
from pydantic import BaseModel

KBM_ENV_BASE = "KBM_"

_KBM_HOME = f"{KBM_ENV_BASE}HOME"
_meta = metadata("kbm")


class _AppMetadata(BaseModel):
    name: str = _meta["Name"]
    version: str = _meta["Version"]
    description: str = _meta["Summary"]

    @cached_property
    def home(self) -> Path:
        """KBM home directory ($KBM_HOME or platform default)."""
        env = (
            dotenv.dotenv_values(".kbm.env").get(_KBM_HOME)
            or dotenv.dotenv_values(".env").get(_KBM_HOME)
            or os.environ.get(_KBM_HOME)
        )

        if env:
            return Path(env).expanduser().resolve()
        return Path(typer.get_app_dir(self.name))

    @cached_property
    def memories_path(self) -> Path:
        """Directory for managed memory config files."""
        return self.home / "memories"

    @cached_property
    def data_root(self) -> Path:
        """Root directory for memory data storage."""
        return self.home / "data"

    def global_config_files(self) -> list[Path]:
        """List of global memory config files."""
        return sorted([f for f in self.memories_path.glob("*") if f.is_file()])

    def local_config_files(self) -> list[Path]:
        """List of local memory config files in current directory."""
        return sorted([f for f in Path.cwd().glob(".kbm*") if f.is_file()])


app_settings = _AppMetadata()
"""Application metadata singleton."""
