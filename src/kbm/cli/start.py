"""Start command."""

import typer

from kbm.config import Engine, MemoryConfig, Transport
from kbm.config.settings import MemorySettings
from kbm.mcp.server import run_server

from . import MemoryNameArg, app, console
from .helpers import print_status, setup_file_logging


@app.command()
def start(
    name: str = MemoryNameArg,
    engine: Engine | None = typer.Option(None, "-e", "--engine", help="Memory engine."),
    transport: Transport | None = typer.Option(None, "-t", "--transport"),
    host: str | None = typer.Option(None, "-H", "--host"),
    port: int | None = typer.Option(None, "-p", "--port"),
) -> None:
    """Start the MCP server."""
    try:  # Load config
        memory = MemoryConfig.from_name(name)
    except FileNotFoundError:
        from .init import create_memory

        # Create new config with defaults
        console.print(f"[yellow]Memory '{name}' not found. Creating new memory...[/]")
        memory = create_memory(MemorySettings(name=name))

    # Handle CLI overrides
    if engine:
        memory.engine = engine
    if transport:
        memory.transport = transport
    if host:
        memory.host = host
    if port:
        memory.port = port

    # Start server with file logging
    print_status(memory)
    setup_file_logging(memory.settings.log_file)
    run_server(memory)
