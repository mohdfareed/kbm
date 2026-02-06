"""Engine wrapper for canonical persistence."""

__all__ = ["CanonicalEngineWrapper"]

import logging

from kbm.engine import EngineProtocol, Operation
from kbm.models import (
    DeleteResponse,
    InfoResponse,
    InsertResponse,
    ListResponse,
    QueryResponse,
    RecordSummary,
)
from kbm.store.canonical import CanonicalStore


class CanonicalEngineWrapper(EngineProtocol):
    """Wraps an engine to add canonical storage for missing operations."""

    def __init__(
        self,
        engine: EngineProtocol,
        store: CanonicalStore,
        logger: logging.Logger | None = None,
    ) -> None:
        self._engine = engine
        self._store = store
        self._engine_ops = engine.supported_operations
        self._logger = logger or logging.getLogger(__name__)

    @property
    def supported_operations(self) -> frozenset[Operation]:
        """Engine ops plus canonical-provided ops."""
        canonical_ops = {
            Operation.INSERT,
            Operation.INSERT_FILE,
            Operation.DELETE,
            Operation.LIST_RECORDS,
        }
        return self._engine_ops | canonical_ops

    async def info(self) -> InfoResponse:
        self._logger.debug("Fetching engine info...")

        try:
            return await self._engine.info()
        except Exception as e:
            self._logger.error(f"Error getting engine info: {e}")

        count = await self._store.count_records()
        return InfoResponse(engine="unknown", records=count)

    async def query(self, query: str, top_k: int = 10) -> QueryResponse:
        self._logger.debug(f"Querying engine with query: {query}")

        try:
            return await self._engine.query(query, top_k)
        except Exception as e:
            self._logger.error(f"Error querying engine: {e}")
            return QueryResponse(results=[], query=query, total=0)

    async def insert(self, content: str, doc_id: str | None = None) -> InsertResponse:
        self._logger.debug("Inserting record with ID: {doc_id}")
        rid = await self._store.insert_record(content, doc_id)

        if Operation.INSERT in self._engine_ops:
            try:
                return await self._engine.insert(content, rid)
            except Exception as e:
                self._logger.error(f"Error inserting into engine: {e}")
        return InsertResponse(id=rid)

    async def insert_file(
        self, file_path: str, content: str | None = None, doc_id: str | None = None
    ) -> InsertResponse:
        self._logger.debug(f"Inserting file with ID: {doc_id}")
        rid, path = await self._store.insert_file(file_path, content, doc_id)

        if Operation.INSERT_FILE in self._engine_ops:
            try:
                return await self._engine.insert_file(str(path), doc_id=rid)
            except Exception as e:
                self._logger.error(f"Error inserting file into engine: {e}")
        return InsertResponse(id=rid, message="Stored")

    async def delete(self, record_id: str) -> DeleteResponse:
        self._logger.debug(f"Deleting record with ID: {record_id}")
        found = await self._store.delete_record(record_id)

        if Operation.DELETE in self._engine_ops:
            try:
                return await self._engine.delete(record_id)
            except Exception as e:
                self._logger.error(f"Error deleting from engine: {e}")

        return DeleteResponse(
            id=record_id,
            found=found,
            message="Deleted" if found else "Not found",
        )

    async def list_records(self, limit: int = 100, offset: int = 0) -> ListResponse:
        self._logger.debug(f"Listing records with limit={limit}, offset={offset}")

        if Operation.LIST_RECORDS in self._engine_ops:
            try:
                return await self._engine.list_records(limit, offset)
            except Exception as e:
                self._logger.error(f"Error listing records from engine: {e}")

        records = await self._store.list_records(limit, offset)
        total = await self._store.count_records()

        summaries = [
            RecordSummary(
                id=r.id,
                created_at=r.created_at,
                content_type=r.content_type,
                preview=r.content[:100] + "..." if len(r.content) > 100 else r.content,
            )
            for r in records
        ]

        return ListResponse(records=summaries, total=total, limit=limit, offset=offset)
