"""Helper functions and utilities."""

__all__ = [
    "LazyGroup",
    "find_file",
]

import importlib
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import click
import typer
from typer.core import TyperGroup  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from app.config import Engine


# MARK: File utilities


def find_file(names: Iterable[str]) -> Path | None:
    """Search for file progressively up the directory tree."""
    current = Path.cwd().resolve()
    while True:
        for name in names:
            path = current / name

            try:
                if path.is_file():
                    return path
            except PermissionError:
                return None

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


# MARK: Lazy loading CLI group


class LazyGroup(TyperGroup):  # type: ignore[misc]
    """Custom Typer group that loads engine subcommands lazily based on config.

    Subcommands are registered via the class variable `lazy_subcommands`, which
    maps command names to a dict of {Engine: "module.attr"} import paths.
    The appropriate engine's commands are loaded based on current settings.
    """

    # Maps subcommand name -> {engine: "module.attr"}
    lazy_subcommands: ClassVar[dict[str, dict["Engine", str]]] = {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name: str) -> click.Command:
        """Load the appropriate engine's command based on current settings."""
        from app.config import get_settings, init_settings

        # Ensure settings are initialized (may be called before callback for --help)
        try:
            settings = get_settings()
        except RuntimeError:
            init_settings(None)
            settings = get_settings()

        engine_map = self.lazy_subcommands[cmd_name]

        if settings.engine not in engine_map:
            raise click.ClickException(
                f"Engine '{settings.engine.value}' does not support '{cmd_name}'"
            )

        import_path = engine_map[settings.engine]
        mod_name, attr = import_path.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        typer_app: typer.Typer = getattr(mod, attr)

        # Convert Typer app to Click group
        return typer.main.get_command(typer_app)
