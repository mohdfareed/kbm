"""MCP server implementation."""

from fastmcp import FastMCP

from config import settings

mcp = FastMCP(settings.server_name)


@mcp.tool
def test() -> str:
    """Test tool to verify the MCP server is working."""
    return "MCP server is working!"
