"""MCP server."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP, settings

from kbm.auth import build_auth_provider
from kbm.config import MemoryConfig, Transport
from kbm.engines import get_engine

logger = logging.getLogger(__name__)


def build_server(config: MemoryConfig) -> FastMCP:
    """Build an MCP server for a memory."""
    logger.info(f"Initializing '{config.name}' MCP server...")
    settings.show_server_banner = False

    # Build engine and canonical store
    engine, store = get_engine(config)

    # Close the canonical store on shutdown
    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            print()  # Newline after shutdown message
            logger.info("Closing canonical store...")
            await store.close()

    # Build mcp server and authorization provider
    auth_provider = build_auth_provider(config)
    mcp = FastMCP(
        name=config.name,
        instructions=config.instructions,
        auth=auth_provider,
        lifespan=lifespan,
    )

    # Register supported tools
    for op in engine.supported_operations:
        logger.debug(f"Adding tool: {op.method_name}")
        mcp.add_tool(getattr(engine, op.method_name))

    return mcp


def run_server(config: MemoryConfig) -> None:
    """Run the MCP server."""
    mcp = build_server(config)

    try:  # Run the mcp server
        run_mcp_app(mcp, config)
    except KeyboardInterrupt:
        logger.info(f"MCP server '{config.name}' stopped.")


def run_mcp_app(mcp: FastMCP, config: MemoryConfig) -> None:
    match config.transport:
        case Transport.STDIO:
            logger.info("Starting MCP server over stdio...")
            mcp.run(transport="stdio")

        case Transport.HTTP:
            url = f"{config.host}:{config.port}"
            logger.info(f"Starting MCP server at {url}...")

            mcp.run(
                transport="http",
                host=config.host,
                port=config.port,
                uvicorn_config={"log_config": None},
            )

        case _:  # Should never happen due to validation
            raise NotImplementedError(f"Unsupported transport: {config.transport}")
