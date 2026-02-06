"""Chat history engine - simple text search over canonical store."""

__all__ = ["ChatHistoryEngine"]

import logging
from typing import TYPE_CHECKING

from kbm.engine import EngineProtocol, Operation
from kbm.models import (
    DeleteResponse,
    InfoResponse,
    InsertResponse,
    ListResponse,
    QueryResponse,
    QueryResult,
)
from kbm.store import CanonicalStore

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


class ChatHistoryEngine(EngineProtocol):
    logger = logging.getLogger(__name__)

    def __init__(self, config: "MemoryConfig", store: CanonicalStore) -> None:
        self.logger.info("Initializing Chat History engine...")
        self._store = store

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset({Operation.INFO, Operation.QUERY})

    async def info(self) -> InfoResponse:
        count = await self._store.count_records()
        return InfoResponse(engine="chat-history", records=count)

    async def query(self, query: str, top_k: int = 10) -> QueryResponse:
        records = await self._store.search_records(query, top_k)
        results = [
            QueryResult(id=r.id, content=r.content, created_at=r.created_at)
            for r in records
        ]
        return QueryResponse(results=results, query=query, total=len(results))

    async def insert(self, content: str, doc_id: str | None = None) -> InsertResponse:
        raise NotImplementedError("Handled by canonical layer.")

    async def insert_file(
        self, file_path: str, content: str | None = None, doc_id: str | None = None
    ) -> InsertResponse:
        raise NotImplementedError("Handled by canonical layer.")

    async def delete(self, record_id: str) -> DeleteResponse:
        raise NotImplementedError("Handled by canonical layer.")

    async def list_records(self, limit: int = 100, offset: int = 0) -> ListResponse:
        raise NotImplementedError("Handled by canonical layer.")
