"""MCP server."""

__all__ = ["run_server"]

import logging

from fastmcp import FastMCP, settings

from kbm.config import MemoryConfig, Transport
from kbm.engines import get_engine

logger = logging.getLogger(__name__)


def run_server(config: MemoryConfig) -> None:
    """Run the MCP server."""
    logger.info(f"Initializing '{config.server_name}' MCP server...")
    settings.show_server_banner = False

    mcp = FastMCP(name=config.server_name, instructions=config.instructions)
    engine = get_engine(config)

    for op in engine.supported_operations:
        logger.debug(f"Adding tool: {op.method_name}")
        mcp.add_tool(getattr(engine, op.method_name))

    try:
        run_mcp_app(mcp, config)
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user.")


def run_mcp_app(mcp: FastMCP, config: MemoryConfig) -> None:
    """Run the MCP application server."""
    match config.transport:
        case Transport.STDIO:
            logger.info("Starting MCP server over stdio...")
            mcp.run(transport="stdio")

        case Transport.HTTP:
            logger.info(f"Starting MCP server at {config.host}:{config.port}...")
            mcp.run(
                transport="http",
                host=config.host,
                port=config.port,
                uvicorn_config={"log_config": None},
            )

        case _:  # Should never happen due to validation in MemoryConfig
            raise NotImplementedError(f"Unsupported transport: {config.transport}")
