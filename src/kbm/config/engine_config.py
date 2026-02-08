"""Engine configurations and enums."""

from enum import Enum

from pydantic import BaseModel


class Engine(str, Enum):
    """Available storage engines."""

    CHAT_HISTORY = "chat-history"
    RAG_ANYTHING = "rag-anything"


class RAGAnythingConfig(BaseModel):
    """RAG-Anything engine configuration."""

    class Provider(str, Enum):
        ANTHROPIC = "anthropic"
        AZURE = "azure"
        OPENAI = "openai"

    # Provider settings
    provider: Provider = Provider.OPENAI
    api_key: str | None = None  # env var default set by provider
    base_url: str | None = None  # env var default set by provider
    api_version: str | None = None  # Azure only

    # Model settings
    query_mode: str = "mix"
    llm_model: str = "gpt-4o-mini"
    vision_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 3072
