"""Init command."""

import typer

from kbm.config import Engine, MemoryConfig, MemorySettings, app_settings

from . import MemoryNameArg, app, console
from .helpers import print_summary


def create_memory(settings: MemorySettings, **kwargs) -> MemoryConfig:
    """Create a new memory config file and return the config."""
    settings.ensure_dirs()

    if (template := app_settings.template_path) and template.exists():
        memory = MemoryConfig.from_template(template, settings=settings, **kwargs)
    else:
        memory = MemoryConfig.default(settings=settings, **kwargs)

    memory.settings.config_file.write_text(memory.dump_yaml(full=False))
    return memory


@app.command()
def init(
    name: str = MemoryNameArg,
    engine: Engine = typer.Option(Engine.CHAT_HISTORY, "-e", "--engine"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite if exists."),
) -> None:
    """Create a new memory."""
    settings = MemorySettings(name=name)
    if settings.config_file.exists() and not force:
        raise FileExistsError(f"Memory already exists: {name}")

    memory = create_memory(settings, engine=engine)
    console.print(f"Initialized '{name}' at: [bold]{memory.settings.config_file}[/]")
    print_summary(memory)
