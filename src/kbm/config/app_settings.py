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
_KBM_DEBUG = f"{KBM_ENV_BASE}DEBUG"
_meta = metadata("kbm")


def _get_env(key: str) -> str | None:
    return (
        os.environ.get(key)
        or dotenv.dotenv_values(".kbm.env").get(key)
        or dotenv.dotenv_values(".env").get(key)
    )


class _AppMetadata(BaseModel):
    _debug: bool = False

    name: str = _meta["Name"]
    version: str = _meta["Version"]
    description: str = _meta["Summary"]

    @property
    def debug(self) -> bool:
        """Debug mode ($KBM_DEBUG or $DEBUG)."""
        return self._debug or (_get_env(_KBM_DEBUG) or _get_env("DEBUG")) in (
            "1",
            "true",
            "True",
        )

    @debug.setter
    def debug(self, new_data):
        self._debug = new_data

    @cached_property
    def home(self) -> Path:
        """KBM home directory ($KBM_HOME or platform default)."""
        if env := _get_env(_KBM_HOME):
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
        return sorted([f for f in Path.cwd().glob(".kbm.*") if f.is_file()])


app_settings = _AppMetadata()
"""Application metadata singleton."""
