"""MCP server."""

__all__ = ["run_server"]

import logging

from fastmcp import FastMCP

from kbm.config import MemoryConfig, Transport
from kbm.engines import get_engine

logger = logging.getLogger(__name__)


def run_server(config: MemoryConfig) -> None:
    """Run the MCP server."""
    logger.info(
        f"Initializing MCP server: "
        f"{config.server_name} ({config.engine.value}) -> "
        + (
            f"{config.host}:{config.port}"
            if config.transport == Transport.HTTP
            else "stdio"
        )
    )

    mcp = FastMCP(name=config.server_name, instructions=config.instructions)
    engine = get_engine(config)

    for op in engine.supported_operations:
        logger.debug(f"Adding tool: {op.method_name}")
        mcp.add_tool(getattr(engine, op.method_name))

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
        case _:
            raise NotImplementedError(f"Unsupported transport: {config.transport}")
