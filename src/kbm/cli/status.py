"""Status command."""

import sys

import typer

from kbm.config import MemoryConfig

from . import MemoryNameArg, app, console
from .helpers import format_config, print_summary


@app.command()
def status(
    name: str = MemoryNameArg,
    full: bool = typer.Option(
        False, "-f", "--full", help="Show all options with defaults."
    ),
    path: bool = typer.Option(False, "-p", "--path", help="Show config file path."),
) -> None:
    """Show memory configuration."""
    cfg = MemoryConfig.from_name(name)

    if path:
        console.print(cfg.file_path)
        sys.exit(0)

    print_summary(cfg)
    console.print("\n[dim]Configuration:[/dim]")

    # Print config options with or without defaults
    for line in format_config(cfg.dump(full=full)):
        console.print(line)
