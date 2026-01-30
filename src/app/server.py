"""MCP server."""

__all__ = ["Transport", "init_server", "start_server"]

from enum import Enum

from fastmcp import FastMCP

from app.config import Engines, get_settings


class Transport(str, Enum):
    """MCP server transport options."""

    stdio = "stdio"
    http = "http"
    stream = "streamable-http"


def init_server() -> FastMCP:
    """Initialize and configure MCP server."""
    settings = get_settings()
    mcp = FastMCP(
        settings.server_name,
        instructions=settings.prompts.server_instructions,
    )

    # Register engine-specific tools
    if settings.engine == Engines.chat_history:
        from engines.chat_history.tools import register

        register(mcp)
    elif settings.engine == Engines.rag_anything:
        from engines.rag_anything.tools import register

        register(mcp)
    else:
        raise ValueError(f"Unknown engine: {settings.engine}")

    return mcp


def start_server(
    mcp: FastMCP,
    transport: Transport,
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Start the MCP server with the specified transport.

    Args:
        mcp: The FastMCP server instance.
        transport: Transport type (stdio, http, or streamable-http).
        host: Host to bind to (HTTP transports only).
        port: Port to bind to (HTTP transports only).
    """
    if transport == Transport.stdio:
        mcp.run(transport=transport.value)
        return

    # HTTP transports require host and port
    settings = get_settings()
    mcp.run(
        transport=transport.value,
        host=host or settings.http_host,
        port=port or settings.http_port,
    )
