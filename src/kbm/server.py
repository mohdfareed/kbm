"""MCP server."""

__all__ = ["run_server"]

import logging

from fastmcp import FastMCP, settings
from fastmcp.server.auth import require_auth
from fastmcp.server.middleware import AuthMiddleware

from kbm.auth import build_auth_provider, build_email_check
from kbm.config import GithubAuthConfig, MemoryConfig, Transport
from kbm.engines import get_engine

logger = logging.getLogger(__name__)


def run_server(config: MemoryConfig) -> None:
    """Run the MCP server."""
    logger.info(f"Initializing '{config.server_name}' MCP server...")
    settings.show_server_banner = False

    # Build server and auth provider if configured
    auth_provider = build_auth_provider(config)
    mcp = FastMCP(
        name=config.server_name,
        instructions=config.instructions,
        auth=auth_provider,
    )

    # Add global auth middleware if GitHub auth is enabled
    github_auth = config.auth if isinstance(config.auth, GithubAuthConfig) else None
    if auth_provider and github_auth:
        access_check = build_email_check(github_auth)
        mcp.add_middleware(AuthMiddleware(auth=[require_auth, access_check]))

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
