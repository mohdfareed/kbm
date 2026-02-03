"""Chat history engine - JSON file storage."""

__all__ = ["ChatHistoryEngine"]

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig

_log = logging.getLogger(__name__)


class ChatHistoryEngine(EngineProtocol):
    """Simple JSON file storage. Each record is a .json file."""

    def __init__(self, config: "MemoryConfig") -> None:
        self.data_dir = config.engine_data_path
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset(
            {
                Operation.INFO,
                Operation.QUERY,
                Operation.INSERT,
                Operation.DELETE,
                Operation.LIST_RECORDS,
            }
        )

    async def info(self) -> str:
        """Get information about the knowledge base."""
        count = len(list(self.data_dir.glob("*.json")))
        return f"Engine: chat-history\nRecords: {count}"

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information."""
        results = []
        for path in self.data_dir.glob("*.json"):
            try:
                record = json.loads(path.read_text())
                if query.lower() in record.get("content", "").lower():
                    results.append(record)
                    if len(results) >= top_k:
                        break
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Skipping %s: %s", path.name, e)

        if not results:
            return "No matching records found."

        return "\n\n".join(
            f"[{r['id']}] {r['created_at']}\n{r['content'][:200]}..."
            if len(r["content"]) > 200
            else f"[{r['id']}] {r['created_at']}\n{r['content']}"
            for r in results
        )

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert text content into the knowledge base."""
        rid = doc_id or str(uuid.uuid4())
        record = {
            "id": rid,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (self.data_dir / f"{rid}.json").write_text(json.dumps(record, indent=2))
        return f"Inserted: {rid}"

    async def delete(self, record_id: str) -> str:
        """Delete a record from the knowledge base by its ID."""
        path = self.data_dir / f"{record_id}.json"
        if not path.exists():
            return f"Not found: {record_id}"
        path.unlink()
        return f"Deleted: {record_id}"

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """List records in the knowledge base."""
        paths = sorted(self.data_dir.glob("*.json"))[offset : offset + limit]
        if not paths:
            return "No records found."

        lines = []
        for path in paths:
            try:
                r = json.loads(path.read_text())
                preview = (
                    r["content"][:100] + "..."
                    if len(r["content"]) > 100
                    else r["content"]
                )
                lines.append(f"[{r['id']}] {preview}")
            except (json.JSONDecodeError, IOError):
                lines.append(f"[{path.stem}] <error>")
        return "\n".join(lines)

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Not supported - use rag-anything for files."""
        raise NotImplementedError("Use rag-anything engine for file insertion.")
