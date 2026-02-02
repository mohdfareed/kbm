"""Storage engines."""

__all__ = ["get_engine"]

from app import Engine, EngineProtocol


def get_engine(engine: Engine) -> EngineProtocol:
    """Get an engine instance by type."""
    match engine:
        case Engine.CHAT_HISTORY:
            from engines.chat_history import ChatHistoryEngine

            return ChatHistoryEngine()
        case Engine.RAG_ANYTHING:
            from engines.rag_anything import RAGAnythingEngine

            return RAGAnythingEngine()
