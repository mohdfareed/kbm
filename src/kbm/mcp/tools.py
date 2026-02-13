"""MCP tool surface — binds canonical store + engine into MCP tools.

``MemoryTools`` is the *only* class decorated with ``@tool``.  It owns
the canonical store write, delegates engine-specific work to the
injected ``Engine``, and converts exceptions into ``ToolError``.
"""

__all__: list[str] = []

import logging
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import tool

from kbm import schema
from kbm.engines import BaseEngine
from kbm.store import CanonStore

logger = logging.getLogger(__name__)


class MemoryTools:
    """Concrete MCP tool surface backed by a canonical store and an engine."""

    def __init__(self, engine: BaseEngine, store: CanonStore) -> None:
        self.engine = engine
        self.store = store

    # MARK: Read-only tools

    @tool(
        description=schema.INFO_DESCRIPTION,
        annotations=schema.INFO_ANNOTATIONS,
    )
    async def info(self) -> schema.InfoResponse:
        return await self._call(self.engine.info)

    @tool(
        description=schema.QUERY_DESCRIPTION,
        annotations=schema.QUERY_ANNOTATIONS,
    )
    async def query(
        self, query: schema.QueryText, top_k: schema.TopK = 10
    ) -> schema.QueryResponse:
        return await self._call(self.engine.query, query, top_k)

    @tool(
        description=schema.GET_RECORD_DESCRIPTION,
        annotations=schema.GET_RECORD_ANNOTATIONS,
    )
    async def get_record(self, record_id: schema.RecordId) -> schema.GetRecordResponse:
        return await self._call(self._get_record, record_id)

    @tool(
        description=schema.LIST_RECORDS_DESCRIPTION,
        annotations=schema.LIST_RECORDS_ANNOTATIONS,
    )
    async def list_records(
        self, limit: schema.Limit = 100, offset: schema.Offset = 0
    ) -> schema.ListResponse:
        return await self._call(self._list_records, limit, offset)

    # MARK: Mutation tools

    @tool(
        description=schema.INSERT_DESCRIPTION,
        annotations=schema.INSERT_ANNOTATIONS,
    )
    async def insert(self, content: schema.Content) -> schema.InsertResponse:
        return await self._call(self._insert, content)

    @tool(
        description=schema.INSERT_FILE_DESCRIPTION,
        annotations=schema.INSERT_FILE_ANNOTATIONS,
    )
    async def insert_file(
        self, file_path: schema.FilePath, content: schema.FileContent = None
    ) -> schema.InsertResponse:
        return await self._call(self._insert_file, file_path, content)

    @tool(
        description=schema.DELETE_DESCRIPTION,
        annotations=schema.DELETE_ANNOTATIONS,
    )
    async def delete(self, record_id: schema.RecordId) -> schema.DeleteResponse:
        return await self._call(self._delete, record_id)

    # MARK: Internal implementations

    async def _get_record(self, record_id: str) -> schema.GetRecordResponse:
        await self.store.initialize()
        record = await self.store.get_record(record_id)
        if record is None:
            raise ToolError(f"Record not found: {record_id}")
        return schema.GetRecordResponse(
            id=record.id,
            content=record.content,
            content_type=record.content_type,
            source=record.source,
            created_at=record.created_at,
            found=True,
        )

    async def _list_records(
        self, limit: int = 100, offset: int = 0
    ) -> schema.ListResponse:
        await self.store.initialize()
        records = await self.store.list_records(limit, offset)
        total = await self.store.count_records()
        summaries = [
            schema.RecordSummary(
                id=r.id,
                created_at=r.created_at,
                content_type=r.content_type,
                source=r.source,
                preview=(
                    r.content[:100] + "..." if len(r.content) > 100 else r.content
                ),
            )
            for r in records
        ]
        return schema.ListResponse(
            records=summaries, total=total, limit=limit, offset=offset
        )

    async def _insert(self, content: str) -> schema.InsertResponse:
        await self.store.initialize()
        rid = await self.store.insert_record(content)
        msg = await self.engine.insert(content, rid)
        return schema.InsertResponse(id=rid, message=msg or "Inserted")

    async def _insert_file(
        self, file_path: str, content: str | None = None
    ) -> schema.InsertResponse:
        await self.store.initialize()
        rid, abs_path = await self.store.insert_file(file_path, content)
        msg = await self.engine.insert_file(abs_path, rid)
        return schema.InsertResponse(
            id=rid, message=msg or f"Inserted: {Path(file_path).name}"
        )

    async def _delete(self, record_id: str) -> schema.DeleteResponse:
        await self.store.initialize()
        # Let the engine clean up before we remove the canonical record.
        await self.engine.delete(record_id)
        found = await self.store.delete_record(record_id)
        return schema.DeleteResponse(
            id=record_id,
            found=found,
            message="Deleted" if found else "Not found",
        )

    # MARK: Error boundary

    async def _call(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Invoke *fn* and convert unexpected exceptions to ``ToolError``."""
        try:
            return await fn(*args, **kwargs)
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {fn.__name__}: {e}")
            raise ToolError(str(e)) from e
