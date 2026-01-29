"""Storage engine abstractions and registry."""

__all__ = [
    "Engine",
    "Operation",
    "RAGAnythingEngine",
    "get_engine",
    "get_schemas",
]

from typing import TYPE_CHECKING

from pydantic import BaseModel

from config import EngineType, settings

from .base import Engine, Operation
from .rag_anything import RAGAnythingEngine

if TYPE_CHECKING:
    pass

# Engine type to class mapping
_ENGINE_MAP: dict[EngineType, type[Engine]] = {
    EngineType.RAG_ANYTHING: RAGAnythingEngine,
}

# Active engine instance (singleton)
_engine: Engine | None = None


def get_engine() -> Engine:
    """Get the active engine instance.

    Returns:
        The singleton Engine instance.
    """
    global _engine

    if _engine is None:
        engine_cls = _ENGINE_MAP[settings.engine]
        _engine = engine_cls()

    return _engine


def get_schemas() -> dict[Operation, type[BaseModel]]:
    """Get the parameter schemas for the active engine.

    Returns:
        Dict mapping Operation enum to their Pydantic parameter models.
    """
    return get_engine().get_schemas()
