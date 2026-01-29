"""Server runtime."""

from enum import Enum

from server.mcp import mcp


class Transport(str, Enum):
    """MCP server transport options."""

    stdio = "stdio"
    http = "http"
    stream = "streamable-http"


def start(transport: Transport) -> None:
    """Start the MCP server with the specified transport."""
    mcp.run(transport=transport.value)
