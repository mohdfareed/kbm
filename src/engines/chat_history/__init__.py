"""Chat history engine - simple JSON file storage."""

__all__ = ["ChatHistoryEngine"]

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app import EngineProtocol, Operation, get_settings

logger = logging.getLogger(__name__)


class ChatHistoryEngine(EngineProtocol):
    """Simple chat history engine storing records as JSON files.

    Supports all memory operations: query, insert, insert_file, delete, list.
    Records are stored as individual JSON files in the data directory.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.data_dir = settings.engine_data_dir

    @property
    def supported_operations(self) -> frozenset[Operation]:
        """Chat history supports all operations."""
        return frozenset(
            {
                Operation.INFO,
                Operation.QUERY,
                Operation.INSERT,
                Operation.INSERT_FILE,
                Operation.DELETE,
                Operation.LIST_RECORDS,
            }
        )

    async def info(self) -> str:
        """Get information about the knowledge base."""
        record_count = len(list(self.data_dir.glob("*.json")))
        return (
            f"Engine: chat-history\n"
            f"Data directory: {self.data_dir}\n"
            f"Record count: {record_count}"
        )

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information."""
        results = []

        for path in self.data_dir.glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                content = record.get("content", "")
                if query.lower() in content.lower():
                    results.append(record)
                    if len(results) >= top_k:
                        break
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Skipping corrupted record %s: %s", path.name, e)
                continue

        if not results:
            return "No matching records found."

        output = []
        for r in results:
            content = r["content"]
            preview = f"{content[:200]}..." if len(content) > 200 else content
            output.append(f"[{r['id']}] {r['created_at']}\n{preview}")
        return "\n\n".join(output)

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert text content into the knowledge base."""
        record_id = doc_id or str(uuid.uuid4())

        record = {
            "id": record_id,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        }

        self._save_record(record_id, record)
        return f"Inserted record: {record_id}"

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Insert a file into the knowledge base (PDF, image, etc.)."""
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        content = path.read_text(encoding="utf-8")
        record_id = doc_id or path.stem

        record = {
            "id": record_id,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source_file": str(path), "file_name": path.name},
        }

        self._save_record(record_id, record)
        return f"Inserted file as record: {record_id}"

    async def delete(self, record_id: str) -> str:
        """Delete a record from the knowledge base by its ID."""
        if not self._delete_record(record_id):
            raise ValueError(f"Record not found: {record_id}")
        return f"Deleted record: {record_id}"

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """List records in the knowledge base."""
        records = []
        all_paths = sorted(self.data_dir.glob("*.json"))
        paginated = all_paths[offset : offset + limit]

        for path in paginated:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                records.append(
                    f"[{record['id']}] {record.get('created_at', 'unknown')}"
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Skipping corrupted record %s: %s", path.name, e)
                continue

        if not records:
            return "No records found."

        return "\n".join(records)

    # Internal methods

    def _record_path(self, record_id: str) -> Path:
        return self.data_dir / f"{record_id}.json"

    def _save_record(self, record_id: str, data: dict) -> None:
        path = self._record_path(record_id)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _delete_record(self, record_id: str) -> bool:
        path = self._record_path(record_id)
        if path.exists():
            path.unlink()
            return True
        return False
