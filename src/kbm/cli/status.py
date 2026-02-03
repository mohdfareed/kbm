"""Status command."""

from pathlib import Path

import typer

from kbm.config import MemoryConfig

from .app import cli_app, console


@cli_app.command()
def status(
    name: str | None = typer.Argument(None, help="Memory name or omit for local."),
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Config file path."
    ),
    full: bool = typer.Option(
        False, "--full", help="Include all options with defaults."
    ),
) -> None:
    """Show memory configuration."""
    cfg = MemoryConfig.load(name=name, config=config)

    console.print(f"[bold]{cfg.name}[/bold] ({cfg.engine.value})")
    console.print(f"  Config: {cfg.file_path}")
    console.print(f"  Data:   {cfg.data_path}")
    console.print()
    console.print(cfg.dump(full=full).rstrip())
