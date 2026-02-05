"""Init command."""

from pathlib import Path

import typer

from kbm.config import Engine, MemoryConfig, app_settings

from . import app, console


@app.command()
def init(
    name: str | None = typer.Argument(
        None, help="Memory name. Defaults to current directory name."
    ),
    local: bool = typer.Option(
        False, "--local", help="Create local .kbm.{name}.yaml file."
    ),
    engine: Engine = typer.Option(Engine.CHAT_HISTORY, "-e", "--engine"),
    json: bool = typer.Option(False, "--json", help="Use JSON format instead of YAML."),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite if exists."),
) -> None:
    """Create a new memory."""
    memory_name = name or Path.cwd().name
    ext = "json" if json else "yaml"

    if local:
        config_path = Path.cwd() / f".kbm.{memory_name}.{ext}"
    else:
        config_path = app_settings.memories_path / f"{memory_name}.{ext}"

    if config_path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {config_path}")

    config = MemoryConfig(name=memory_name, file_path=config_path, engine=engine)
    config.data_path.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if json:
        config_path.write_text(config.dump_json())
    else:
        config_path.write_text(config.dump_yaml())

    location = "local" if not config.is_global else "global"
    console.print(
        f"[green]✓[/green] Created {location} memory [bold]{memory_name}[/bold]"
    )
    console.print(f"\tConfig: [dim]{config_path}[/dim]")
    console.print(f"\tData:   [dim]{config.data_path}[/dim]")
