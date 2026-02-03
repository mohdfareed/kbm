"""Init command."""

from pathlib import Path

import typer

from kbm.config import Engine, MemoryConfig, app_metadata

from .app import cli_app, console


@cli_app.command()
def init(
    name: str | None = typer.Argument(
        None, help="Memory name (global) or omit for local."
    ),
    engine: Engine = typer.Option(Engine.CHAT_HISTORY, "-e", "--engine"),
    json: bool = typer.Option(
        False, "--json", help="Output config in JSON format instead of YAML."
    ),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing."),
) -> None:
    """Create a new memory."""
    memory_name = name or Path.cwd().name
    config_path = (
        app_metadata.local_config_path()
        if name is None
        else app_metadata.named_config_path(name)
    )

    if config_path.exists() and not force:
        raise FileExistsError(f"Already exists: {config_path}")

    config = MemoryConfig(name=memory_name, file_path=config_path, engine=engine)
    config.data_path.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if json:
        config_path.write_text(config.dump_json())
    else:
        config_path.write_text(config.dump_yaml())

    location = "global" if config.is_global else "local"
    console.print(f"[green]✓[/green] Created [bold]{memory_name}[/bold] ({location})")
    console.print(f"  [dim]Config:[/dim] {config_path}")
    console.print(f"  [dim]Data:[/dim]   {config.data_path}")
