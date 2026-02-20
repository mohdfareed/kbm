"""Status command."""

import sys

import typer

from kbm.config import MemoryConfig

from . import MemoryNameArg, app, console
from .helpers import dump_display, format_config, print_summary


@app.command()
def status(
    name: str = MemoryNameArg,
    full: bool = typer.Option(
        False, "-f", "--full", help="Show all options with defaults."
    ),
    path: bool = typer.Option(False, "-p", "--path", help="Show config file path."),
) -> None:
    """Show memory configuration."""
    memory = MemoryConfig.from_name(name)

    if path:
        console.print(memory.settings.config_file)
        sys.exit(0)

    print_summary(memory)
    for line in format_config(dump_display(memory, active_only=not full)):
        console.print(f"  {line}")
