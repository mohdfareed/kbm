"""Chat history engine - simple text search over canonical store."""

__all__: list[str] = []

import logging

from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from . import schema
from .base_engine import EngineBase, Operation


class ChatHistoryEngine(EngineBase):
    logger = logging.getLogger(__name__)
    supported_operations = frozenset(Operation)  # all operations

    def __init__(self, config: "MemoryConfig", store: CanonStore) -> None:
        super().__init__(config, store)

    async def _info(self) -> schema.InfoResponse:
        count = await self._store.count_records()
        return schema.InfoResponse(engine=Engine.CHAT_HISTORY.value, records=count)

    async def _query(self, query: str, top_k: int = 10) -> schema.QueryResponse:
        records = await self._store.search_records(query, top_k)
        results = [
            schema.QueryResult(id=r.id, content=r.content, created_at=r.created_at)
            for r in records
        ]
        return schema.QueryResponse(results=results, query=query, total=len(results))
