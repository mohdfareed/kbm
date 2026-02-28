"""CLI package."""

__all__ = ["app", "main"]

import logging
import os
import socket
import sys
from pathlib import Path

import typer
from rich.console import Console

from kbm.config import app_settings

MemoryNameArg = typer.Argument(
    os.environ.get("KBM_NAME") or Path.cwd().name or socket.gethostname(),
    help="Memory name.",
    autocompletion=lambda: [p.stem for p in app_settings.memories],
)

console = Console()
err_console = Console(stderr=True)
logger = logging.getLogger(f"{app_settings.name}.cli")

app = typer.Typer(
    name=app_settings.name,
    help=app_settings.description,
    no_args_is_help=True,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except Exception as e:
        if app_settings.debug:
            logger.error(f"An error occurred: {e}", exc_info=True)
        else:
            err_console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)


@app.callback()
def callback(
    version: bool = typer.Option(
        False, "-v", "--version", help="Show version and exit."
    ),
    debug: bool = typer.Option(
        app_settings.debug, "-d", "--debug", help="Enable debug logging."
    ),
    home: Path | None = typer.Option(
        None, "-r", "--root", help="Override home directory."
    ),
    config: Path | None = typer.Option(
        None,
        "-c",
        "--config",
        help="Path to a memory config file.",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
) -> None:
    """Persistent memory for LLMs via MCP."""
    from .helpers import setup_logging

    app_settings.debug = debug
    if home is not None:
        app_settings.home = home.expanduser().resolve()
    if config is not None:
        app_settings.config_file = config
    setup_logging()

    if version:
        console.print(f"{app_settings.name} {app_settings.version}")
        sys.exit(0)


# MARK: Command Registration

# Register commands (order determines help display)
# isort: off
from kbm.cli import init, start, inspect  # noqa: E402


@app.command()
def version() -> None:
    """Print application version."""
    console.print(app_settings.version)


@app.command()
def home() -> None:
    """Print application home directory."""
    console.print(app_settings.home)


@app.command()
def settings(all=False) -> None:
    """Print application settings."""
    console.print(app_settings.dump_yaml(full=all))


@app.command()
def memory(name: str = MemoryNameArg, all=False) -> None:
    """Print application memory directory."""
    from kbm.config import MemoryConfig

    memory = MemoryConfig.from_name(name)
    console.print(memory.dump_yaml(full=all))
