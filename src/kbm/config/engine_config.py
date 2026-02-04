"""Engine configurations and enums."""

from enum import Enum

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class EngineConfig(BaseModel):
    model_config = SettingsConfigDict(extra="forbid")


class Engine(str, Enum):
    """Available storage engines."""

    CHAT_HISTORY = "chat-history"
    RAG_ANYTHING = "rag-anything"


# MARK: Engine-specific Configs


class ChatHistoryConfig(EngineConfig):
    """Chat history engine configuration."""


class RAGAnythingConfig(EngineConfig):
    """RAG-Anything engine configuration."""

    # OpenAI settings
    api_key: str | None = None
    base_url: str | None = None

    # Model settings
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 3072
    query_mode: str = "hybrid"

    # Capabilities
    enable_image_processing: bool = True
    enable_table_processing: bool = True
    enable_equation_processing: bool = True
