"""Status command."""

from pathlib import Path

import typer

from kbm.config import MemoryConfig

from . import app, console


@app.command()
def status(
    name: str | None = typer.Argument(
        None, help="Memory name (global) or omit to use local memory."
    ),
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Config file path to override name."
    ),
    full: bool = typer.Option(
        False, "--full", help="Include all options with defaults."
    ),
) -> None:
    """Show memory configuration."""
    if name and config:
        raise typer.BadParameter("Cannot specify both name and config.")

    if config:
        cfg = MemoryConfig.from_config(config)
    else:
        cfg = MemoryConfig.from_name(name)

    console.print(f"[bold]{cfg.name}[/bold] [dim]• {cfg.engine.value}[/dim]")
    console.print(f"  [dim]Config:[/dim] {cfg.file_path}")
    console.print(f"  [dim]Data:[/dim]   {cfg.data_path}")
    console.print()

    console.print("[bold]Configuration:[/bold]")
    for key, value in cfg.dump(full=full).items():
        console.print(f"[dim]{key}:[/dim] {value}")
