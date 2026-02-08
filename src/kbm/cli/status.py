"""Status command."""

import typer

from kbm.config import MemoryConfig

from . import MemoryNameArg, app, console
from .helpers import print_summary


@app.command()
def status(
    name: str = MemoryNameArg,
    full: bool = typer.Option(
        False, "-f", "--full", help="Show all options with defaults."
    ),
) -> None:
    """Show memory configuration."""
    cfg = MemoryConfig.from_name(name)
    print_summary(cfg)

    # Print config options with or without defaults
    console.print("\n[dim]Configuration:[/dim]")
    for key, value in cfg.dump(full=full).items():
        console.print(f"{key}={value}")
