"""CLI entry point."""

__all__ = ["cli"]

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich import print

from app.config import (
    APP_NAME,
    DESCRIPTION,
    VERSION,
    ConfigFormat,
    Settings,
    Transport,
    get_settings,
    init_settings,
)
from app.helpers import configure_logging, error
from app.server import init_server, start_server

cli = typer.Typer(
    name=APP_NAME,
    help=DESCRIPTION,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        print(f"{APP_NAME} {VERSION}")
        raise typer.Exit()


def _config_callback(config: Path | None) -> Path | None:
    init_settings(config)
    return config


@cli.callback()
def callback(
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            "-d",
            help="Enable debug logging.",
            callback=lambda v: configure_logging(v),
            is_eager=True,
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to config file.",
            callback=_config_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Knowledge Base Manager - Persistent memory for LLMs via MCP."""
    pass


@cli.command()
def start(
    transport: Annotated[
        Transport | None,
        typer.Argument(help="Server transport type."),
    ] = None,
    host: Annotated[
        str | None,
        typer.Option("--host", "-H", help="HTTP transport host."),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option("--port", "-p", help="HTTP transport port."),
    ] = None,
) -> None:
    """Start the MCP server."""
    settings = get_settings()
    effective_transport = transport or settings.transport

    match effective_transport:
        case Transport.STDIO:
            print(
                f"[bold]Starting[/bold] {settings.server_name} "
                f"[dim](engine={settings.engine.value})[/dim]"
            )
        case Transport.HTTP | Transport.STREAMABLE_HTTP:
            effective_host = host or settings.http_host
            effective_port = port or settings.http_port
            print(
                f"[bold]Starting[/bold] {settings.server_name} "
                f"[dim](engine={settings.engine.value})[/dim] "
                f"on {effective_host}:{effective_port}"
            )
        case _:
            error(f"Unsupported transport: {effective_transport}")

    mcp = init_server()
    start_server(mcp, transport, host, port)


@cli.command()
def config(
    fmt: Annotated[
        ConfigFormat,
        typer.Option("-f", "--format", help="Output format."),
    ] = ConfigFormat.JSON,
    all_engines: Annotated[
        bool,
        typer.Option("--all", help="Include all engine configs."),
    ] = False,
) -> None:
    """Show current configuration."""
    settings = get_settings()
    if all_engines:
        data = settings.model_dump(mode="json")
    else:
        data = settings.model_dump_active(mode="json")
    print(fmt.dumps(data))


@cli.command()
def init(
    path: Annotated[
        Path | None,
        typer.Option("-p", "--path", help="Output file path."),
    ] = None,
    fmt: Annotated[
        ConfigFormat,
        typer.Option("-f", "--format", help="Output format."),
    ] = ConfigFormat.YAML,
    force: Annotated[
        bool,
        typer.Option("-F", "--force", help="Overwrite existing file."),
    ] = False,
) -> None:
    """Create a config file with default settings."""
    output = path or Path(fmt.filename)

    if output.exists() and not force:
        error(f"File already exists: {output}. Use --force to overwrite.")

    # Exclude config_file since it's runtime-determined, not user-configurable
    defaults = Settings().model_dump(mode="json", exclude={"config_file"})
    output.parent.mkdir(parents=True, exist_ok=True)
    fmt.write(output, defaults)

    print(f"[bold]Created[/bold] config file: {output}")


@cli.command()
def info() -> None:
    """Show engine and data path information."""
    from engines import get_engine

    settings = get_settings()
    engine = get_engine(settings.engine)

    ops = sorted(op.name.lower() for op in engine.supported_operations)

    print(f"[bold]Engine:[/bold]     {settings.engine.value}")
    print(f"[bold]Server:[/bold]     {settings.server_name}")
    print(f"[bold]Data:[/bold]       {settings.data_dir}")
    print(f"[bold]Engine data:[/bold] {settings.engine_data_dir}")
    print(f"[bold]Operations:[/bold]\n\t - {'\n\t - '.join(ops)}")


@cli.command()
def query(
    query_text: Annotated[str, typer.Argument(help="Search query")],
    top_k: Annotated[int, typer.Option("--top-k", "-k", help="Max results")] = 10,
) -> None:
    """Search the knowledge base."""
    from engines import get_engine

    settings = get_settings()
    engine = get_engine(settings.engine)

    result = asyncio.run(engine.query(query_text, top_k=top_k))
    print(result)
