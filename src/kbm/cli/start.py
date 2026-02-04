"""Start command."""

from pathlib import Path

import typer

from kbm.config import MemoryConfig, Transport
from kbm.server import run_server

from . import app, console


@app.command()
def start(
    name: str | None = typer.Argument(
        None, help="Memory name (global) or omit to use local memory."
    ),
    config: Path | None = typer.Option(
        None, "-c", "--config", help="Config file path to override name."
    ),
    transport: Transport | None = typer.Option(None, "-t", "--transport"),
    host: str | None = typer.Option(None, "-H", "--host"),
    port: int | None = typer.Option(None, "-p", "--port"),
) -> None:
    """Start the MCP server."""
    if name and config:
        raise typer.BadParameter("Cannot specify both name and config.")

    if config:
        cfg = MemoryConfig.from_config(config)
    else:
        cfg = MemoryConfig.from_name(name)

    cfg.engine_data_path.mkdir(parents=True, exist_ok=True)
    if transport:
        cfg.transport = transport
    if host:
        cfg.host = host
    if port:
        cfg.port = port

    engine_text = f"• {cfg.engine.value} • {cfg.transport.value}"
    console.print(f"[bold]{cfg.name}[/bold] [dim]{engine_text}[/dim]")
    if cfg.transport == Transport.HTTP:
        console.print(f"[dim]Listening on[/dim] http://{cfg.host}:{cfg.port}")
    console.print()

    run_server(cfg)
