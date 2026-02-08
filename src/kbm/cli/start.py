"""Start command."""

import typer

from kbm.config import Engine, MemoryConfig, Transport
from kbm.server import run_server

from . import MemoryNameArg, app
from .helpers import print_status, setup_file_logging


@app.command()
def start(
    name: str = MemoryNameArg,
    engine: Engine | None = typer.Option(
        None, "-e", "--engine", help="Override engine for this session"
    ),
    transport: Transport | None = typer.Option(None, "-t", "--transport"),
    host: str | None = typer.Option(None, "-H", "--host"),
    port: int | None = typer.Option(None, "-p", "--port"),
    create: bool = typer.Option(
        False, "-c", "--create", help="Create memory if it doesn't exist"
    ),
) -> None:
    """Start the MCP server."""
    overrides = {}
    if engine is not None:
        overrides["engine"] = engine

    try:  # Load config
        cfg = MemoryConfig.from_name(name, **overrides)
    except FileNotFoundError:
        if not create:
            raise  # No config found
        from .init import create_memory

        # Create new config with defaults
        cfg = create_memory(name, engine or Engine.CHAT_HISTORY)

    # Handle CLI overrides
    if transport:
        cfg.transport = transport
    if host:
        cfg.host = host
    if port:
        cfg.port = port

    # Start server with file logging
    print_status(cfg)
    setup_file_logging(cfg.log_file)
    run_server(cfg)
