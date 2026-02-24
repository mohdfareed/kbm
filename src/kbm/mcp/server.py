"""MCP server."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP, settings

from kbm.auth import build_auth_provider
from kbm.config import Engine, MemoryConfig, Transport
from kbm.engines.chat_history import ChatHistoryEngine
from kbm.engines.mem0 import Mem0Engine
from kbm.engines.rag_anything import RAGAnythingEngine
from kbm.store import CanonStore

from .tools import MemoryTools

logger = logging.getLogger(__name__)


def run_server(memory: MemoryConfig) -> None:
    """Run the MCP server."""
    logger.info(f"Initializing '{memory.settings.name}' MCP server...")
    mcp = build_server(memory)

    try:  # Run the mcp server
        settings.show_server_banner = False
        match memory.transport:
            case Transport.STDIO:
                logger.info("Starting MCP server over stdio...")
                mcp.run(transport="stdio")

            case Transport.HTTP:
                path = memory.path.strip("/") or None
                url = f"{memory.host}:{memory.port}"
                if path:
                    url += f"/{path}"
                logger.info(f"Starting MCP server over HTTP at {url}...")
                mcp.run(
                    transport="http",
                    host=memory.host,
                    port=memory.port,
                    path=f"/{path}" if path else None,
                    uvicorn_config={"log_config": None},
                )

            case _:  # Should never happen due to validation
                raise NotImplementedError(f"Unsupported transport: {memory.transport}")
    except KeyboardInterrupt:
        logger.info(f"MCP server '{memory.settings.name}' stopped.")


def build_server(memory: MemoryConfig) -> FastMCP:
    """Build the MCP server for the given memory config."""
    # Create canonical store (shared by all engines)
    store = CanonStore(
        memory.settings.database_url,
        attachments_path=memory.settings.attachments_path,
    )

    # Create engine based on config
    match memory.engine:
        case Engine.CHAT_HISTORY:
            engine = ChatHistoryEngine(memory, store)
        case Engine.MEM0:
            engine = Mem0Engine(memory)
        case Engine.RAG_ANYTHING:
            engine = RAGAnythingEngine(memory)
        case _:
            raise NotImplementedError(f"Unsupported engine: {memory.engine}")
    tools = MemoryTools(engine, store)

    # Close the canonical store on shutdown
    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            print()  # Newline after shutdown message
            logger.info("Closing canonical store...")
            await tools.store.close()

    # Build mcp server and authorization provider
    auth_provider = build_auth_provider(memory)
    mcp = FastMCP(
        name=memory.settings.name,
        instructions=memory.mcp_instructions,
        auth=auth_provider,
        lifespan=lifespan,
    )

    # Register only the operations supported by this engine
    for op in tools.engine.supported_operations:
        logger.debug(f"Adding tool: {op.method_name}")
        mcp.add_tool(getattr(tools, op.method_name))

    return mcp
