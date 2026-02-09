"""Storage engines."""

__all__ = ["ChatHistoryEngine", "RAGAnythingEngine", "get_engine"]


from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from .base_engine import EngineBase
from .chat_history import ChatHistoryEngine
from .rag_anything import RAGAnythingEngine


def get_engine(memory: MemoryConfig) -> tuple[EngineBase, CanonStore]:
    """Get engine instance and its canonical store for config."""
    store = CanonStore(
        memory.settings.database_url, attachments_path=memory.settings.attachments_path
    )

    match memory.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            return ChatHistoryEngine(memory, store), store
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            return RAGAnythingEngine(memory, store), store
        case _:
            raise NotImplementedError(f"Unsupported engine: {memory.config.engine}")
