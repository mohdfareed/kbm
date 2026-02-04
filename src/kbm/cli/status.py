"""Status command."""

from pathlib import Path

import typer

from kbm.config import MemoryConfig

from . import app, console


@app.command()
def status(
    name: str | None = typer.Argument(None, help="Memory name (omit for local)."),
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Config file path."
    ),
    full: bool = typer.Option(False, "--full", help="Show all options with defaults."),
) -> None:
    """Show memory configuration."""
    if name and config:
        raise typer.BadParameter("Specify either name or --config, not both.")

    cfg = MemoryConfig.from_config(config) if config else MemoryConfig.from_name(name)

    console.print(f"[bold]{cfg.name}[/bold] [dim]• {cfg.engine.value}[/dim]")
    console.print(f"\tConfig: [dim]{cfg.file_path}[/dim]")
    console.print(f"\tData:   [dim]{cfg.data_path}[/dim]")
    console.print()

    console.print("Configuration:")
    for key, value in cfg.dump(full=full).items():
        console.print(f"[dim]{key}=[/dim]{value}")
