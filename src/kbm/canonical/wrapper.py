"""Engine wrapper for canonical persistence."""

__all__ = ["CanonicalEngineWrapper", "with_canonical"]

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kbm.canonical.store import CanonicalStore
from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


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

    async def info(self) -> str:
        """Get info from engine."""
        try:
            return await self._engine.info()
        except Exception as e:
            self._logger.error(f"Error getting engine info: {e}")
            return "Engine info not available."

    async def query(self, query: str, top_k: int = 10) -> str:
        """Query the underlying engine."""
        try:
            return await self._engine.query(query, top_k)
        except Exception as e:
            self._logger.error(f"Error querying engine: {e}")
            return "Query failed."

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert to canonical, then to engine if supported."""
        rid = await self._store.insert_record(content, doc_id)
        if Operation.INSERT in self._engine_ops:
            try:
                await self._engine.insert(content, rid)
            except Exception as e:
                self._logger.error(f"Error inserting into engine: {e}")
        return f"Inserted: {rid}"

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Store file in canonical, delegate to engine if supported."""
        path = Path(file_path).expanduser().resolve()
        rid = await self._store.insert_record(
            content=str(path),
            doc_id=doc_id,
            content_type="file_ref",
            source=str(path),
        )

        await self._store.insert_attachment(
            record_id=rid,
            file_name=path.name,
            file_path=str(path),
            mime_type=None,
            size_bytes=path.stat().st_size if path.exists() else None,
        )

        if Operation.INSERT_FILE in self._engine_ops:
            try:
                return await self._engine.insert_file(file_path, rid)
            except Exception as e:
                self._logger.error(f"Error inserting file into engine: {e}")
        return f"Stored: {rid}"

    async def delete(self, record_id: str) -> str:
        """Delete from canonical, and engine if supported."""
        found = await self._store.delete_record(record_id)
        if Operation.DELETE in self._engine_ops:
            try:
                await self._engine.delete(record_id)
            except Exception as e:
                self._logger.error(f"Error deleting from engine: {e}")
        return f"Deleted: {record_id}" if found else f"Not found: {record_id}"

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """List from engine if supported, else from canonical."""
        if Operation.LIST_RECORDS in self._engine_ops:
            try:
                return await self._engine.list_records(limit, offset)
            except Exception as e:
                self._logger.error(f"Error listing records from engine: {e}")

        records = await self._store.list_records(limit, offset)
        if not records:
            return "No records found."

        lines = []
        for r in records:
            preview = r.content[:100] + "..." if len(r.content) > 100 else r.content
            lines.append(f"[{r.id}] {r.created_at.isoformat()} ({r.content_type})")
            lines.append(f"  {preview}")
        return "\n".join(lines)


def with_canonical(config: "MemoryConfig", engine: EngineProtocol) -> EngineProtocol:
    """Wrap engine with canonical storage."""
    store = CanonicalStore(config.canonical_url)
    return CanonicalEngineWrapper(engine, store)
