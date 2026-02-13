"""Chat history engine — simple full-text search over the canonical store."""

__all__: list[str] = []

import logging
from pathlib import Path

from kbm import schema
from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from .base import BaseEngine, Operation

logger = logging.getLogger(__name__)


class ChatHistoryEngine(BaseEngine):
    """Full-text search engine backed by SQLite FTS5.

    This is the simplest engine: it adds no indexing side-effects.
    Queries use the canonical store's built-in FTS5 full-text search
    with BM25 ranking.
    """

    supported_operations = frozenset(
        {
            Operation.INFO,
            Operation.QUERY,
            Operation.INSERT,
            Operation.DELETE,
            Operation.GET_RECORD,
            Operation.LIST_RECORDS,
        }
    )  # text-only, no file support

    def __init__(self, memory: MemoryConfig, store: CanonStore) -> None:
        logger.info(f"Initializing {memory.engine} engine...")
        self._store = store

    async def info(self) -> schema.InfoResponse:
        count = await self._store.count_records()
        return schema.InfoResponse(
            engine=Engine.CHAT_HISTORY.value,
            records=count,
            instructions=(
                "Full-text search engine using SQLite FTS5. "
                "Queries support tokenized word matching, prefix search, and "
                "phrase queries. Results are ranked by BM25 relevance. "
                "Use specific keywords, phrases in quotes, or prefix matches with *."
            ),
        )

    async def query(self, query: str, top_k: int = 10) -> schema.QueryResponse:
        records = await self._store.search_records(query, top_k)
        results = [
            schema.QueryResult(id=r.id, content=r.content, created_at=r.created_at)
            for r in records
        ]
        return schema.QueryResponse(results=results, query=query, total=len(results))

    async def insert(self, content: str, record_id: str) -> str | None:
        return None  # FTS5 index is maintained by SQLite triggers

    async def insert_file(self, path: Path, record_id: str) -> str | None:
        return None  # Files are maintained by local file system and SQLite db

    async def delete(self, record_id: str) -> None:
        pass  # FTS5 cleanup is handled by SQLite triggers
