"""Authentication setup for MCP server."""

__all__ = ["WRITE_METHOD_NAMES", "build_auth_provider", "build_email_check"]

import logging

from fastmcp.server.auth import AuthContext
from fastmcp.server.auth.providers.github import GitHubProvider

from kbm.config import AuthProvider, GithubAuthConfig, MemoryConfig, Transport
from kbm.engine import Operation

logger = logging.getLogger(__name__)

# Write operation method names
WRITE_METHOD_NAMES = frozenset(
    {
        Operation.INSERT.method_name,
        Operation.INSERT_FILE.method_name,
        Operation.DELETE.method_name,
    }
)


def build_auth_provider(config: MemoryConfig) -> GitHubProvider | None:
    """Build auth provider based on config."""
    if config.auth is None or config.auth.provider == AuthProvider.NONE:
        return None

    if config.transport != Transport.HTTP:
        logger.warning("Auth is only supported for HTTP transport, ignoring.")
        return None

    match config.auth.provider:
        case AuthProvider.GITHUB:
            if not isinstance(config.auth, GithubAuthConfig):
                raise ValueError("GitHub auth requires GithubAuthConfig")

            base_url = config.auth.base_url or f"http://{config.host}:{config.port}"
            logger.info(f"Enabling GitHub OAuth with base URL: {base_url}")

            return GitHubProvider(
                client_id=config.auth.client_id,
                client_secret=config.auth.client_secret,
                base_url=base_url,
            )

        case AuthProvider.NONE:
            return None

        case _:
            raise ValueError(f"Unsupported auth provider: {config.auth.provider}")


def build_email_check(auth_config: GithubAuthConfig):
    """Build auth check for email allowlist and read-only enforcement."""

    def check_access(ctx: AuthContext) -> bool:
        if ctx.token is None:
            return False

        email = ctx.token.claims.get("email")
        if not email:
            logger.warning("No email in token claims, denying access.")
            return False

        # Check allowlist (empty = allow all authenticated users)
        if auth_config.allowed_emails and email not in auth_config.allowed_emails:
            return False

        # Check read-only restriction for write operations
        if email in auth_config.read_only_emails:
            tool_name = getattr(ctx.component, "name", "")
            if tool_name in WRITE_METHOD_NAMES:
                logger.debug(f"Blocking {tool_name} for read-only user: {email}")
                return False

        return True

    return check_access
