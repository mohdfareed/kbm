"""Chat history engine - simple text search over canonical store."""

__all__ = ["ChatHistoryEngine"]

from typing import TYPE_CHECKING

from kbm.canonical import CanonicalStore
from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


class ChatHistoryEngine(EngineProtocol):
    """Simple text search. Storage handled by canonical layer."""

    def __init__(self, config: "MemoryConfig") -> None:
        self._store = CanonicalStore(config.canonical_url)

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset({Operation.INFO, Operation.QUERY})

    async def info(self) -> str:
        """Get information about the knowledge base."""
        count = await self._store.count_records()
        return f"Engine: chat-history\nRecords: {count}"

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information."""
        records = await self._store.search_records(query, top_k)
        if not records:
            return "No matching records found."

        lines = []
        for r in records:
            preview = r.content[:200] + "..." if len(r.content) > 200 else r.content
            lines.append(f"[{r.id}] {r.created_at.isoformat()}\n{preview}")
        return "\n\n".join(lines)

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Handled by canonical layer."""
        raise NotImplementedError

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Handled by canonical layer."""
        raise NotImplementedError

    async def delete(self, record_id: str) -> str:
        """Handled by canonical layer."""
        raise NotImplementedError

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """Handled by canonical layer."""
        raise NotImplementedError
