"""CLI entry point."""

__all__ = ["cli"]

import json
from pathlib import Path

import typer
import yaml
from rich import print, print_json

from app.config import (
    APP_NAME,
    DESCRIPTION,
    VERSION,
    Engine,
    Format,
    Settings,
    get_settings,
    init_settings,
)
from app.helpers import LazyGroup
from app.server import Transport, init_server, start_server

# MARK: CLI setup

cli = typer.Typer(
    name=APP_NAME,
    help=DESCRIPTION,
    no_args_is_help=True,
    cls=LazyGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Register lazy subcommands (loaded based on engine in settings)
LazyGroup.lazy_subcommands["memory"] = {
    Engine.chat_history: "engines.chat_history.commands.app",
    Engine.rag_anything: "engines.rag_anything.commands.app",
}


# MARK: CLI commands


def _config_callback(config: Path | None) -> Path | None:
    """Load config before command resolution."""
    init_settings(config)
    return config


@cli.callback()
def callback(
    config: Path | None = typer.Option(
        None,
        "-c",
        "--config",
        help="Path to config file",
        callback=_config_callback,
        is_eager=True,
    ),
) -> None:
    """CLI application entry point."""
    pass  # Config already loaded by eager callback


@cli.command()
def start() -> None:
    """Start the MCP server."""
    settings = get_settings()
    typer.echo(f"Starting {settings.server_name} server (engine={settings.engine})...")

    mcp = init_server()
    start_server(mcp, Transport.stdio)


@cli.command()
def version() -> None:
    """Show the version number."""
    typer.echo(f"{APP_NAME} {VERSION}")


@cli.command()
def config(
    fmt: Format = typer.Option(Format.json, "-f", "--format", help="Output format"),
) -> None:
    """Show current configuration."""
    settings = get_settings()
    data = settings.model_dump(mode="json")

    if fmt == Format.yaml:
        print(yaml.safe_dump(data, sort_keys=False).rstrip())
    elif fmt == Format.json:
        print_json(json.dumps(data, indent=2))
    elif fmt == Format.env:
        lines = _settings_to_env(data)
        print("\n".join(lines))


@cli.command()
def init(
    path: Path | None = typer.Option(None, "-p", "--path", help="Output file path"),
    fmt: Format = typer.Option(Format.yaml, "-f", "--format", help="Output format"),
    force: bool = typer.Option(False, "-F", "--force", help="Overwrite existing file"),
) -> None:
    """Create a config file with default settings."""
    output = path or Path(fmt.filename)
    if output.exists() and not force:
        typer.echo("File already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    # Get default settings and prep for writing
    defaults = Settings().model_dump(mode="json", exclude_computed_fields=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    env_lines = _settings_to_env(defaults)

    # Write config file
    if fmt == Format.yaml:
        output.write_text(yaml.safe_dump(defaults, sort_keys=False))
    elif fmt == Format.json:
        output.write_text(json.dumps(defaults, indent=2) + "\n")
    elif fmt == Format.env:
        output.write_text("\n".join(env_lines) + "\n")

    typer.echo(f"Created config file: {output}")


def _settings_to_env(data: dict, prefix: str = "KBM") -> list[str]:
    """Convert settings dict to environment variable lines."""
    lines: list[str] = []
    for key, value in data.items():
        env_key = f"{prefix}_{key}".upper()
        if isinstance(value, dict):
            lines.extend(_settings_to_env(value, env_key))
        elif value is not None:
            lines.append(f"{env_key}={value}")
    return lines
    return lines
