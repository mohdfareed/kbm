"""MCP server."""

__all__ = ["Transport", "init_server", "start_server"]

from enum import Enum

from fastmcp import FastMCP

from app.config import get_settings
from app.engine import CAPABILITY_METHODS, REQUIRED_METHODS
from engines import get_engine


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

    engine = get_engine(settings.engine.value)
    _register_tools(mcp, engine)

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


def _register_tools(mcp: FastMCP, engine) -> None:
    """Register tools based on engine capabilities.

    FastMCP introspects method signatures automatically - no manual
    parameter handling needed. Just pass the bound method.
    """
    for method in REQUIRED_METHODS:
        mcp.add_tool(getattr(engine, method.__name__))

    for cap, method in CAPABILITY_METHODS.items():
        if cap in engine.capabilities:
            mcp.add_tool(getattr(engine, method.__name__))

    # Engine-specific extras
    for extra_tool in engine.get_extra_tools():
        mcp.add_tool(extra_tool)
