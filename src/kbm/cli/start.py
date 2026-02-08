"""Start command."""

import typer

from kbm.config import MemoryConfig, Transport
from kbm.server import run_server

from . import MemoryNameArg, app
from .helpers import print_status, setup_file_logging


@app.command()
def start(
    name: str = MemoryNameArg,
    transport: Transport | None = typer.Option(None, "-t", "--transport"),
    host: str | None = typer.Option(None, "-H", "--host"),
    port: int | None = typer.Option(None, "-p", "--port"),
) -> None:
    """Start the MCP server."""
    cfg = MemoryConfig.from_name(name)

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
