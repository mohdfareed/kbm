"""Storage engines."""

__all__ = ["get_engine"]

import logging
from typing import TYPE_CHECKING

from kbm.config import Engine
from kbm.engine import EngineProtocol
from kbm.store import CanonicalStore

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


def with_canonical(store: CanonicalStore, engine: EngineProtocol) -> EngineProtocol:
    """Wrap engine with canonical storage."""
    from kbm.engines.canonical import CanonicalEngineWrapper

    return CanonicalEngineWrapper(
        engine, store, logger=logging.getLogger(engine.__class__.__name__)
    )


def get_engine(config: "MemoryConfig") -> EngineProtocol:
    """Get engine instance for config, wrapped with canonical storage."""
    store = CanonicalStore(config.canonical_url, uploads_path=config.uploads_path)

    match config.engine:
        case Engine.CHAT_HISTORY:
            from kbm.engines.chat_history import ChatHistoryEngine

            return with_canonical(store, ChatHistoryEngine(config, store))
        case Engine.RAG_ANYTHING:
            from kbm.engines.rag_anything import RAGAnythingEngine

            return with_canonical(store, RAGAnythingEngine(config))
        case Engine.FEDERATION:
            from kbm.engines.federation import FederationEngine

            return FederationEngine(config)  # No canonical wrap
