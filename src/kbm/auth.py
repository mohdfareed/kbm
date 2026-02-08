"""Authentication setup for MCP server."""

import logging

from fastmcp.server.auth import AuthProvider as LibAuthProvider
from fastmcp.server.auth.providers.github import GitHubProvider

from kbm.config import MemoryConfig, Transport
from kbm.config.auth_config import AuthProvider

logger = logging.getLogger(__name__)


def build_auth_provider(config: MemoryConfig) -> LibAuthProvider | None:
    """Build auth provider based on config."""
    if config.transport != Transport.HTTP and config.auth != AuthProvider.NONE:
        raise ValueError("Authentication is only supported for HTTP transport.")
    if config.transport != Transport.HTTP:
        return None  # No auth for non-HTTP transports

    match config.auth:
        case AuthProvider.NONE:
            logger.warning("No authentication configured for MCP server.")
            return None
        case AuthProvider.GITHUB:
            return build_github_auth_provider(config)


def build_github_auth_provider(config: MemoryConfig) -> GitHubProvider:
    gh = config.github_auth

    if not gh.client_id or not gh.client_secret:
        raise ValueError("GitHub authentication requires client_id and client_secret.")
    base_url = gh.base_url or f"http://{config.host}:{config.port}"

    logger.info(f"Enabling GitHub OAuth with base URL: {base_url}")
    return GitHubProvider(
        client_id=gh.client_id,
        client_secret=gh.client_secret,
        base_url=base_url,
    )
