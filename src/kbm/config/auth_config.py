"""Authentication configuration for HTTP transport."""

from enum import Enum

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class AuthProvider(str, Enum):
    """Available authentication providers."""

    NONE = "none"  # No authentication
    GITHUB = "github"  # GitHub OAuth


class AuthConfig(BaseModel):
    """Base authentication configuration."""

    model_config = SettingsConfigDict(extra="forbid")
    provider: AuthProvider = AuthProvider.NONE


class GithubAuthConfig(AuthConfig):
    """GitHub OAuth authentication configuration."""

    provider: AuthProvider = AuthProvider.GITHUB
    client_id: str  # GitHub OAuth App client ID
    client_secret: str  # GitHub OAuth App client secret
    base_url: str | None = None  # Server base URL for OAuth callback

    # Access control
    allowed_emails: list[str] = []  # empty = allow all
    read_only_emails: list[str] = []  # empty = no read-only users
