"""MCP server."""

__all__ = ["Transport", "init_server", "start_server"]

from enum import Enum

from fastmcp import FastMCP

from app.config import get_settings
from app.engine import Operation


class Transport(str, Enum):
    """MCP server transport options."""

    STDIO = "stdio"
    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"


def init_server() -> FastMCP:
    """Initialize and configure MCP server."""
    from engines import get_engine

    settings = get_settings()
    mcp = FastMCP(
        settings.server_name,
        instructions=settings.instructions,
    )

    engine = get_engine(settings.engine)
    supported = engine.supported_operations

    # Register only supported operations as tools
    for op in Operation:
        if op in supported:
            method = getattr(engine, op.method_name)
            mcp.add_tool(method)

    return mcp


def start_server(
    mcp: FastMCP,
    transport: Transport,
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Start the MCP server with the specified transport."""
    settings = get_settings()

    match transport:
        case Transport.STDIO:
            mcp.run(transport=transport.value)
        case Transport.HTTP | Transport.STREAMABLE_HTTP:
            mcp.run(
                transport=transport.value,
                host=host or settings.http_host,
                port=port or settings.http_port,
            )
