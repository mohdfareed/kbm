"""Helper functions and utilities."""

__all__ = ["configure_logging", "console", "error", "find_file", "settings_to_env"]

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def error(message: str) -> NoReturn:
    """Print error message and exit."""
    print(f"[red]Error:[/red] {message}")
    raise typer.Exit(1)


def configure_logging(debug: bool) -> None:
    """Configure logging for CLI commands."""
    if not debug:
        logging.disable(logging.CRITICAL)
        return

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(RichHandler(console=console))


def find_file(names: Iterable[str | Path]) -> Path | None:
    """Search for file progressively up the directory tree."""
    current = Path.cwd().resolve()
    while True:
        for name in names:
            path = current / name

            try:
                if path.is_file():
                    return path
            except PermissionError:
                logging.warning("Permission denied accessing %s", path)
                return None

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def settings_to_env(data: dict, prefix: str) -> list[str]:
    """Convert settings dict to environment variable lines."""
    lines: list[str] = []
    for key, value in data.items():
        env_key = f"{prefix}_{key}".upper()
        if isinstance(value, dict):
            lines.extend(settings_to_env(value, env_key))
        elif value is not None:
            lines.append(f"{env_key}={value}")
    return lines
