"""Start command."""

from pathlib import Path

import typer

from kbm.config import MemoryConfig, Transport
from kbm.server import run_server

from . import app, console


@app.command()
def start(
    name: str | None = typer.Argument(None, help="Memory name (omit for local)."),
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Config file path."
    ),
    transport: Transport | None = typer.Option(None, "-t", "--transport"),
    host: str | None = typer.Option(None, "-H", "--host"),
    port: int | None = typer.Option(None, "-p", "--port"),
) -> None:
    """Start the MCP server."""
    if name and config:
        raise typer.BadParameter("Specify either name or --config, not both.")
    cfg = MemoryConfig.from_config(config) if config else MemoryConfig.from_name(name)

    if transport:
        cfg.transport = transport
    if host:
        cfg.host = host
    if port:
        cfg.port = port

    # Header
    console.print(f"[bold]{cfg.name}[/bold] [dim]• {cfg.engine.value}[/dim]")
    if cfg.transport == Transport.HTTP:
        console.print(f"[dim]http://{cfg.host}:{cfg.port}[/dim]")
    console.print()

    run_server(cfg)
