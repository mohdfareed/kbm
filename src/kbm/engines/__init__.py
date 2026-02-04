"""Storage engines."""

__all__ = ["get_engine"]

from typing import TYPE_CHECKING

from kbm.canonical import with_canonical
from kbm.config import Engine
from kbm.engine import EngineProtocol

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


def get_engine(config: "MemoryConfig") -> EngineProtocol:
    """Get engine instance for config, wrapped with canonical storage."""
    match config.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            engine = ChatHistoryEngine(config)
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            engine = RAGAnythingEngine(config)
        case Engine.FEDERATION:
            from kbm.engines.federation import FederationEngine

            return FederationEngine(config)  # No canonical wrap

    # Wrap with canonical storage for durability
    return with_canonical(config, engine)
