"""Engine base class - template-method pattern with error boundary.

Subclasses declare ``supported_operations`` and override hook methods.
The public template methods (decorated with ``@tool``) are registered as
MCP tools by the server.  All model-facing text (descriptions, annotations,
parameter schemas) lives in ``engines/tool_schema.py``.
"""

__all__: list[str] = []

import inspect
import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import tool

from kbm.config import MemoryConfig
from kbm.store import CanonStore

from . import schema

# MARK: Types & constants


class Operation(Enum):
    """Engine operations. Names match EngineBase public method names."""

    INFO = auto()
    QUERY = auto()
    INSERT = auto()
    INSERT_FILE = auto()
    DELETE = auto()
    LIST_RECORDS = auto()

    @property
    def method_name(self) -> str:
        return self.name.lower()

    @property
    def hook_name(self) -> str:
        return f"_{self.name.lower()}"


class EngineBase(ABC):
    """Base class for memory engines."""

    logger: logging.Logger

    supported_operations: frozenset[Operation]
    """Operations this engine exposes as MCP tools."""

    # MARK: Initialization

    def __init__(self, memory: MemoryConfig, store: CanonStore) -> None:
        self.logger.info(f"Initializing {memory.engine} engine...")
        self._memory = memory
        self._store = store

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return  # skip validation on abstract subclasses

        for op in cls.supported_operations:
            if not hasattr(cls, op.hook_name):
                raise TypeError(
                    f"{cls.__name__} declares Operation.{op.name} "
                    f"but has no '{op.hook_name}' hook method."
                )

    # MARK: Template methods
    # Registered as MCP tools by the server

    @tool(description=schema.INFO_DESCRIPTION, annotations=schema.INFO_ANNOTATIONS)
    async def info(self) -> schema.InfoResponse:
        return await self._call_hook(self._info)

    @tool(description=schema.QUERY_DESCRIPTION, annotations=schema.QUERY_ANNOTATIONS)
    async def query(
        self, query: schema.QueryText, top_k: schema.TopK = 10
    ) -> schema.QueryResponse:
        return await self._call_hook(self._query, query, top_k)

    @tool(description=schema.INSERT_DESCRIPTION, annotations=schema.INSERT_ANNOTATIONS)
    async def insert(self, content: schema.Content) -> schema.InsertResponse:
        return await self._call_hook(self._insert, content)

    @tool(
        description=schema.INSERT_FILE_DESCRIPTION,
        annotations=schema.INSERT_FILE_ANNOTATIONS,
    )
    async def insert_file(
        self, file_path: schema.FilePath, content: schema.FileContent = None
    ) -> schema.InsertResponse:
        return await self._call_hook(self._insert_file, file_path, content)

    @tool(description=schema.DELETE_DESCRIPTION, annotations=schema.DELETE_ANNOTATIONS)
    async def delete(self, record_id: schema.RecordId) -> schema.DeleteResponse:
        return await self._call_hook(self._delete, record_id)

    @tool(
        description=schema.LIST_RECORDS_DESCRIPTION,
        annotations=schema.LIST_RECORDS_ANNOTATIONS,
    )
    async def list_records(
        self, limit: schema.Limit = 100, offset: schema.Offset = 0
    ) -> schema.ListResponse:
        return await self._call_hook(self._list_records, limit, offset)

    # MARK: Hook methods
    # Subclasses override these

    @abstractmethod
    async def _info(self) -> schema.InfoResponse: ...

    @abstractmethod
    async def _query(self, query: str, top_k: int) -> schema.QueryResponse: ...

    async def _insert(
        self, content: str, doc_id: str | None = None
    ) -> schema.InsertResponse:
        rid = await self._store.insert_record(content, doc_id)
        return schema.InsertResponse(id=rid)

    async def _insert_file(
        self,
        file_path: str,
        content: str | None = None,
        doc_id: str | None = None,
    ) -> schema.InsertResponse:
        rid, _path = await self._store.insert_file(file_path, content, doc_id)
        return schema.InsertResponse(id=rid)

    async def _delete(self, record_id: str) -> schema.DeleteResponse:
        found = await self._store.delete_record(record_id)
        return schema.DeleteResponse(
            id=record_id,
            found=found,
            message="Deleted" if found else "Not found",
        )

    async def _list_records(
        self, limit: int = 100, offset: int = 0
    ) -> schema.ListResponse:
        records = await self._store.list_records(limit, offset)
        total = await self._store.count_records()
        summaries = [
            schema.RecordSummary(
                id=r.id,
                created_at=r.created_at,
                content_type=r.content_type,
                preview=(
                    r.content[:100] + "..." if len(r.content) > 100 else r.content
                ),
            )
            for r in records
        ]
        return schema.ListResponse(
            records=summaries, total=total, limit=limit, offset=offset
        )

    # MARK: Helper methods

    async def _call_hook(self, hook: Any, *args: Any, **kwargs: Any) -> Any:
        """Call a hook method, converting exceptions to ToolError."""
        try:
            return await hook(*args, **kwargs)
        except ToolError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in {hook.__name__}: {e}")
            raise ToolError(str(e)) from e
