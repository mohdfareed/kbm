"""Chat history engine - simple JSON file storage."""

__all__ = ["ChatHistoryEngine", "get_engine"]

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

_engine: "ChatHistoryEngine | None" = None


def get_engine() -> "ChatHistoryEngine":
    """Get or create the engine instance."""
    global _engine
    if _engine is None:
        _engine = ChatHistoryEngine()
    return _engine


class ChatHistoryEngine:
    """Simple chat history engine storing records as JSON files."""

    def __init__(self) -> None:
        """Initialize the chat history engine."""
        self.config = settings.chat_history
        self.data_dir = Path(self.config.data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # MARK: - Public methods

    async def query(self, query: str, **kwargs: Any) -> str:
        """Search records for matching content.

        Simple substring search across all records.
        """
        top_k = kwargs.get("top_k", 10)
        results = []

        for path in self.data_dir.glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                content = record.get("content", "")
                if query.lower() in content.lower():
                    results.append(record)
                    if len(results) >= top_k:
                        break
            except (json.JSONDecodeError, IOError):
                continue

        if not results:
            return "No matching records found."

        output = []
        for r in results:
            output.append(
                f"[{r['id']}] {r['created_at']}\n{r['content'][:200]}..."
            )
        return "\n\n".join(output)

    async def insert(self, content: str, **kwargs: Any) -> str:
        """Insert content into the knowledge base."""
        doc_id = kwargs.get("doc_id") or str(uuid.uuid4())

        record = {
            "id": doc_id,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": kwargs.get("metadata", {}),
        }

        self._save_record(doc_id, record)
        return doc_id

    async def insert_file(self, file_path: str, **kwargs: Any) -> str:
        """Insert a file's content into the knowledge base."""
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        doc_id = kwargs.get("doc_id") or path.stem

        return await self.insert(
            content,
            doc_id=doc_id,
            metadata={"source_file": str(path), "file_name": path.name},
        )

    async def delete(self, record_id: str) -> None:
        """Delete a record from the knowledge base."""
        if not self._delete_record(record_id):
            raise ValueError(f"Record not found: {record_id}")

    async def list_records(self, **kwargs: Any) -> list[dict]:
        """List all records in the knowledge base."""
        limit = kwargs.get("limit", 100)
        offset = kwargs.get("offset", 0)

        records = []
        for i, path in enumerate(sorted(self.data_dir.glob("*.json"))):
            if i < offset:
                continue
            if len(records) >= limit:
                break
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                # Return summary, not full content
                records.append(
                    {
                        "id": record["id"],
                        "created_at": record.get("created_at"),
                        "content_preview": record.get("content", "")[:100],
                    }
                )
            except (json.JSONDecodeError, IOError):
                continue

        return records

    async def info(self) -> dict:
        """Get engine information."""
        record_count = len(list(self.data_dir.glob("*.json")))
        return {
            "engine": "chat-history",
            "data_dir": str(self.data_dir),
            "record_count": record_count,
        }

    # MARK: - Internal methods

    def _record_path(self, record_id: str) -> Path:
        """Get path for a record file."""
        return self.data_dir / f"{record_id}.json"

    def _load_record(self, record_id: str) -> dict | None:
        """Load a record from disk."""
        path = self._record_path(record_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_record(self, record_id: str, data: dict) -> None:
        """Save a record to disk."""
        path = self._record_path(record_id)
        path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def _delete_record(self, record_id: str) -> bool:
        """Delete a record from disk."""
        path = self._record_path(record_id)
        if path.exists():
            path.unlink()
            return True
        return False
