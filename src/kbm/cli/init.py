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
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing."),
) -> None:
    """Create a new memory."""
    memory_name = name or Path.cwd().name
    config_path = (
        app_metadata.named_config_path(name)
        if name
        else app_metadata.local_config_path()
    )

    if config_path.exists() and not force:
        raise typer.BadParameter(f"Already exists: {config_path}")

    config = MemoryConfig(name=memory_name, file_path=config_path, engine=engine)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config.dump())
    config.data_path.mkdir(parents=True, exist_ok=True)
    console.print(f"Created {config_path}")
