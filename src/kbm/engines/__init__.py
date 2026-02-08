"""Storage engines."""

__all__ = ["ChatHistoryEngine", "RAGAnythingEngine", "get_engine"]


from kbm.config import Engine, MemoryConfig
from kbm.store import CanonicalStore

from .base_engine import EngineBase
from .chat_history import ChatHistoryEngine
from .rag_anything import RAGAnythingEngine


def get_engine(config: MemoryConfig) -> EngineBase:
    """Get engine instance for config."""
    store = CanonicalStore(
        config.database_url, attachments_path=config.attachments_path
    )

    match config.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            return ChatHistoryEngine(config, store)
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            return RAGAnythingEngine(config, store)
        case _:
            raise NotImplementedError(f"Unsupported engine: {config.engine}")
