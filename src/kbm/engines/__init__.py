"""Storage engines."""

__all__ = ["get_engine"]

from typing import TYPE_CHECKING

from kbm.config import Engine
from kbm.engine import EngineProtocol

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


def get_engine(config: "MemoryConfig") -> EngineProtocol:
    """Get engine instance for config."""
    match config.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            return ChatHistoryEngine(config)
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            return RAGAnythingEngine(config)
