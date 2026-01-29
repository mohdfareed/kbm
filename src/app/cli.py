"""CLI entry point."""

__all__ = ["cli"]

import json
from pathlib import Path

import typer
from rich import print_json

from app.config import (
    APP_NAME,
    DESCRIPTION,
    VERSION,
    Engine,
    get_settings,
    init_settings,
)
from app.server import Transport, init_server, start_server

cli = typer.Typer(
    name=APP_NAME,
    help=DESCRIPTION,
    context_settings={"help_option_names": ["-h", "--help"]},
)


# MARK: CLI commands


@cli.callback()
def callback(
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Path to config file"
    ),
) -> None:
    """CLI application entry point."""
    init_settings(config)
    settings = get_settings()

    # Register engine-specific commands after settings are initialized
    if settings.engine == Engine.chat_history:
        from engines.chat_history.commands import app as memory_app

        cli.add_typer(memory_app)
    elif settings.engine == Engine.rag_anything:
        from engines.rag_anything.commands import app as memory_app

        cli.add_typer(memory_app)
    else:
        raise ValueError(f"Unknown engine: {settings.engine}")


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
def config() -> None:
    """Show current configuration."""
    settings = get_settings()
    data = settings.model_dump(mode="json")
    print_json(json.dumps(data, indent=2))
