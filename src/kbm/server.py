"""MCP server."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP, settings

from kbm.auth import build_auth_provider
from kbm.config import MemoryConfig, Transport
from kbm.engines import get_engine

logger = logging.getLogger(__name__)


def build_server(memory: MemoryConfig) -> FastMCP:
    """Build an MCP server for a memory."""
    logger.info(f"Initializing '{memory.settings.name}' MCP server...")
    settings.show_server_banner = False

    # Build engine and canonical store
    engine, store = get_engine(memory)

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
    auth_provider = build_auth_provider(memory)
    mcp = FastMCP(
        name=memory.settings.name,
        instructions=memory.instructions,
        auth=auth_provider,
        lifespan=lifespan,
    )

    # Register supported tools
    for op in engine.supported_operations:
        logger.debug(f"Adding tool: {op.method_name}")
        mcp.add_tool(getattr(engine, op.method_name))

    return mcp


def run_server(memory: MemoryConfig) -> None:
    """Run the MCP server."""
    mcp = build_server(memory)

    try:  # Run the mcp server
        run_mcp_app(mcp, memory)
    except KeyboardInterrupt:
        logger.info(f"MCP server '{memory.settings.name}' stopped.")


def run_mcp_app(mcp: FastMCP, memory: MemoryConfig) -> None:
    match memory.transport:
        case Transport.STDIO:
            logger.info("Starting MCP server over stdio...")
            mcp.run(transport="stdio")

        case Transport.HTTP:
            url = f"{memory.host}:{memory.port}"
            logger.info(f"Starting MCP server at {url}...")

            mcp.run(
                transport="http",
                host=memory.host,
                port=memory.port,
                uvicorn_config={"log_config": None},
            )

        case _:  # Should never happen due to validation
            raise NotImplementedError(f"Unsupported transport: {memory.transport}")
