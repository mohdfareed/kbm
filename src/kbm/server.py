"""MCP server."""

__all__ = ["run_server"]

from fastmcp import FastMCP

from kbm.config import MemoryConfig, Transport
from kbm.engines import get_engine


def run_server(config: MemoryConfig) -> None:
    """Run the MCP server."""
    mcp = FastMCP(config.name, instructions=config.instructions)
    engine = get_engine(config)

    for op in engine.supported_operations:
        mcp.add_tool(getattr(engine, op.method_name))

    match config.transport:
        case Transport.STDIO:
            mcp.run(transport="stdio")
        case Transport.HTTP:
            mcp.run(transport="http", host=config.host, port=config.port)
