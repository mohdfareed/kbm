"""CLI entry point."""

__all__ = ["cli"]

import json

import typer
from rich import print_json

from app.config import APP_NAME, DESCRIPTION, VERSION, settings
from app.server import Transport

cli = typer.Typer(name=APP_NAME, help=DESCRIPTION)

# Register engine-specific commands
if settings.engine == "chat-history":
    from engines.chat_history.commands import app as memory_app

    cli.add_typer(memory_app)
elif settings.engine == "rag-anything":
    from engines.rag_anything.commands import app as memory_app

    cli.add_typer(memory_app)
else:
    raise ValueError(f"Unknown engine: {settings.engine}")


# MARK: CLI commands


@cli.callback()
def callback() -> None:
    """CLI application entry point."""
    pass


@cli.command()
def start(transport: Transport = Transport.stdio) -> None:
    """Start the MCP server."""
    start(transport=transport)


@cli.command()
def version() -> None:
    """Show the version number."""
    typer.echo(f"{APP_NAME} {VERSION}")


@cli.command()
def config() -> None:
    """Show current configuration."""
    data = settings.model_dump(mode="json")
    print_json(json.dumps(data, indent=2))
