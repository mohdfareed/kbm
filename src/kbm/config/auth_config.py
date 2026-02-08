"""Authentication configuration."""

import os
from enum import Enum

from pydantic import BaseModel


class AuthProvider(str, Enum):
    """Available authentication providers."""

    NONE = "none"
    GITHUB = "github"


class GithubAuthConfig(BaseModel):
    """GitHub OAuth authentication configuration."""

    client_id: str | None = os.environ.get("GITHUB_CLIENT_ID")
    client_secret: str | None = os.environ.get("GITHUB_CLIENT_SECRET")
    base_url: str | None = None
