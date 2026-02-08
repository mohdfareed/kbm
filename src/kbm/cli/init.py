"""Init command."""

import typer

from kbm.config import Engine, MemoryConfig, app_settings

from . import MemoryNameArg, app, console
from .helpers import print_summary


@app.command()
def init(
    name: str = MemoryNameArg,
    engine: Engine = typer.Option(Engine.CHAT_HISTORY, "-e", "--engine"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite if exists."),
) -> None:
    """Create a new memory."""
    config_path = app_settings.memories_path / f"{name}.yaml"
    if config_path.exists() and not force:
        raise FileExistsError(f"Memory already exists: {name}")

    # Create config with defaults and save to file
    config = MemoryConfig(file_path=config_path, name=name, engine=engine)
    config_path.write_text(config.dump_yaml(full=False))

    console.print(f"Initialized '{name}' with engine '{engine}'.")
    print_summary(config)
