"""MCP server."""

__all__ = ["init_server", "start_server", "Transport"]

from enum import Enum

from fastmcp import FastMCP

from app.config import Engine, get_settings


class Transport(str, Enum):
    """MCP server transport options."""

    stdio = "stdio"
    http = "http"
    stream = "streamable-http"


def init_server() -> FastMCP:
    """Initialize and configure MCP server."""
    settings = get_settings()
    mcp = FastMCP(settings.server_name)

    # Register engine-specific tools
    if settings.engine == Engine.chat_history:
        from engines.chat_history.tools import register

        register(mcp)
    elif settings.engine == Engine.rag_anything:
        from engines.rag_anything.tools import register

        register(mcp)
    else:
        raise ValueError(f"Unknown engine: {settings.engine}")

    return mcp


def start_server(mcp: FastMCP, transport: Transport) -> None:
    """Start the MCP server with the specified transport."""
    mcp.run(transport=transport.value)
