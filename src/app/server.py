"""MCP server."""

__all__ = ["mcp", "start", "Transport"]

from enum import Enum

from fastmcp import FastMCP

from app.config import settings

mcp = FastMCP(settings.server_name)


class Transport(str, Enum):
    """MCP server transport options."""

    stdio = "stdio"
    http = "http"
    stream = "streamable-http"


# Register engine-specific tools
if settings.engine == "chat-history":
    from engines.chat_history.tools import register

    register(mcp)
elif settings.engine == "rag-anything":
    from engines.rag_anything.tools import register

    register(mcp)
else:
    raise ValueError(f"Unknown engine: {settings.engine}")


# MARK: Server methods


def start(transport: Transport) -> None:
    """Start the MCP server with the specified transport."""
    mcp.run(transport=transport.value)
