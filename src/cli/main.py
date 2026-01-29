"""CLI entry point."""

import typer

from config import APP_NAME, DESCRIPTION
from server import Transport

from .memory import app as memory_app

app = typer.Typer(name=APP_NAME, help=DESCRIPTION)
app.add_typer(memory_app)


@app.callback()
def callback():
    """CLI application entry point."""
    pass


@app.command()
def start(transport: Transport = Transport.stdio):
    """Start the MCP server."""
    from server import start as start_server

    start_server(transport)
