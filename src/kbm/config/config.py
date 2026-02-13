"""Memory configuration models."""

import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from kbm.config.settings import MemorySettings

from .base import BaseAppConfig

# MARK: Authentication
# =============================================================================


class AuthProvider(str, Enum):
    """Available authentication providers."""

    NONE = "none"
    GITHUB = "github"


class GithubAuthConfig(BaseModel):
    """GitHub OAuth authentication configuration."""

    client_id: str | None = os.environ.get("GITHUB_CLIENT_ID")
    client_secret: str | None = os.environ.get("GITHUB_CLIENT_SECRET")
    base_url: str | None = None


# MARK: Engine
# =============================================================================


class Engine(str, Enum):
    """Available storage engines."""

    CHAT_HISTORY = "chat-history"
    RAG_ANYTHING = "rag-anything"
    MEM0 = "mem0"


class RAGAnythingConfig(BaseModel):
    """RAG-Anything engine configuration."""

    class Provider(str, Enum):
        ANTHROPIC = "anthropic"
        AZURE = "azure"
        OPENAI = "openai"

    # Provider settings
    provider: Provider = Provider.OPENAI
    api_key: str | None = None

    # LLM settings
    query_mode: str = "mix"
    llm_model: str = "gpt-4o-mini"
    vision_model: str = "gpt-4o-mini"

    # Embedding settings
    embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 3072

    # Provider-specific extras (e.g. base_url, api_version, azure_kwargs).
    # Passed through to the underlying LLM/embedding functions as **kwargs.
    config: dict[str, Any] = Field(default_factory=dict)


class Mem0Config(BaseModel):
    """Mem0 engine configuration.

    The ``config`` dict is passed directly to mem0's ``MemoryConfig``.
    All features are enabled by default (vision, reranker, graph store).
    Set a key to ``null`` in YAML to disable it.

    See: https://docs.mem0.ai/open-source/configuration
    """

    config: dict[str, Any] = Field(
        default_factory=lambda: {
            "llm": {
                "provider": "openai",
                "config": {"enable_vision": True},
            },
            "reranker": {
                "provider": "sentence_transformer",
                "config": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
            },
            "graph_store": {
                "provider": "kuzu",
                "config": {},
            },
        }
    )


# MARK: Memory
# =============================================================================


class Transport(str, Enum):
    """Available transport mechanisms."""

    STDIO = "stdio"
    HTTP = "http"


SERVER_INSTRUCTIONS = (
    "This is a knowledge base management tool that provides persistent memory storage. "
    "**IMPORTANT:** Always call the `info` tool first to understand the engine before "
    "attempting to search or interact with the memory."
)


class MemoryConfig(BaseAppConfig):
    """The configuration for a knowledge base memory."""

    settings: MemorySettings = Field(..., exclude=True)

    # memory settings
    instructions: str = (
        "You have access to this project's knowledge base - a persistent memory "
        "that spans conversations, tools, and time. Query it to recall context "
        "from previous sessions, and insert information worth preserving for "
        "future conversations."
    )

    # server settings
    transport: Transport = Transport.STDIO
    host: str = "0.0.0.0"
    port: int = 8000

    # engine settings
    engine: Engine = Engine.CHAT_HISTORY
    rag_anything: RAGAnythingConfig = RAGAnythingConfig()
    mem0: Mem0Config = Mem0Config()

    # authentication settings
    auth: AuthProvider = AuthProvider.NONE
    github_auth: GithubAuthConfig = GithubAuthConfig()

    # Helpers

    @property
    def mcp_instructions(self) -> str:
        """Complete instructions for the MCP server (constant + user config)."""
        return f"{SERVER_INSTRUCTIONS}\n\n{self.instructions}"

    # Factory methods

    @classmethod
    def from_name(cls, name: str, **kwargs) -> "MemoryConfig":
        """Load a named memory config."""
        settings = MemorySettings(name=name)
        return cls._from_file(settings.config_file, settings=settings, **kwargs)

    @classmethod
    def from_template(
        cls, file: Path, settings: MemorySettings, **kwargs
    ) -> "MemoryConfig":
        """Load a memory config from a template file and settings."""
        return cls._from_file(file, settings=settings, **kwargs)

    @classmethod
    def default(cls, settings: MemorySettings, **kwargs) -> "MemoryConfig":
        """Create a default memory config with the given settings."""
        return MemoryConfig(settings=settings, **kwargs)
