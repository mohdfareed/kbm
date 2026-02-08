"""Storage engines."""

__all__ = ["ChatHistoryEngine", "RAGAnythingEngine", "get_engine"]


from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from .base_engine import EngineBase
from .chat_history import ChatHistoryEngine
from .rag_anything import RAGAnythingEngine


def get_engine(config: MemoryConfig) -> tuple[EngineBase, CanonStore]:
    """Get engine instance and its canonical store for config."""
    config.ensure_dirs()
    store = CanonStore(config.database_url, attachments_path=config.attachments_path)

    match config.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            return ChatHistoryEngine(config, store), store
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            return RAGAnythingEngine(config, store), store
        case _:
            raise NotImplementedError(f"Unsupported engine: {config.engine}")
