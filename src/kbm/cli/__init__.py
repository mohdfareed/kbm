"""CLI package."""

__all__ = ["app", "main"]

import sys
from pathlib import Path

import typer
from rich.console import Console

from kbm.config import app_settings

from .helpers import format_config

MemoryNameArg = typer.Argument(Path.cwd().name, help="Memory name.")

console = Console()
err_console = Console(stderr=True)
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
            err_console.print_exception()
        else:
            err_console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)


@app.callback()
def callback(
    debug: bool = typer.Option(
        app_settings.debug, "-d", "--debug", help="Enable debug logging."
    ),
    home: Path | None = typer.Option(
        None, "-r", "--root", help="Override home directory."
    ),
    # Meta options
    settings: bool = typer.Option(
        False, "-s", "--settings", help="Show app settings overrides and exit."
    ),
    full_settings: bool = typer.Option(
        False, "-S", "--all-settings", help="Show all app settings and exit."
    ),
    version: bool = typer.Option(
        False, "-v", "--version", help="Show version and exit."
    ),
) -> None:
    """Persistent memory for LLMs via MCP."""
    from .helpers import setup_logging

    app_settings.debug = debug
    if home is not None:
        app_settings.home = home.expanduser().resolve()
    setup_logging()

    if version:
        console.print(f"{app_settings.name} {app_settings.version}")
        sys.exit(0)

    if settings:
        for line in format_config(app_settings.dump(full=False)):
            console.print(line)
        sys.exit(0)

    if full_settings:
        for line in format_config(app_settings.dump(full=True)):
            console.print(line)
        sys.exit(0)


# MARK: Command Registration

# Register commands (order determines help display)
# isort: off
from kbm.cli import init, start, list, status, delete, inspect  # noqa: E402


@app.command()
def home() -> None:
    """Print application home directory."""
    console.print(app_settings.home)
