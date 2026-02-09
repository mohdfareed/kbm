"""Authentication setup for MCP server."""

import logging

from fastmcp.server.auth import AuthProvider as LibAuthProvider
from fastmcp.server.auth.providers.github import GitHubProvider

from kbm.config import AuthProvider, MemoryConfig, Transport

logger = logging.getLogger(__name__)


def build_auth_provider(memory: MemoryConfig) -> LibAuthProvider | None:
    """Build auth provider based on config."""
    if memory.transport != Transport.HTTP:
        if memory.auth != AuthProvider.NONE:
            raise ValueError("Authentication is only supported for HTTP transport.")
        return None  # non-HTTP transport with no auth

    match memory.auth:
        case AuthProvider.NONE:
            logger.warning("No authentication configured for MCP server.")
            return None
        case AuthProvider.GITHUB:
            return build_github_auth_provider(memory)
        case _:
            raise NotImplementedError(f"Unsupported auth provider: {memory.auth}")


def build_github_auth_provider(memory: MemoryConfig) -> GitHubProvider:
    gh = memory.github_auth

    if not gh.client_id or not gh.client_secret:
        raise ValueError("GitHub authentication requires client_id and client_secret.")
    base_url = gh.base_url or f"http://{memory.host}:{memory.port}"

    logger.info(f"Enabling GitHub OAuth with base URL: {base_url}")
    return GitHubProvider(
        client_id=gh.client_id,
        client_secret=gh.client_secret,
        base_url=base_url,
    )
