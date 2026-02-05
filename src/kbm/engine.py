"""Engine protocol and operations."""

__all__ = ["EngineProtocol", "Operation"]

from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from kbm.models import (
        DeleteResponse,
        InfoResponse,
        InsertResponse,
        ListResponse,
        QueryResponse,
    )


class Operation(Enum):
    """Engine operations. Names match EngineProtocol method names."""

    INFO = auto()
    QUERY = auto()
    INSERT = auto()
    INSERT_FILE = auto()
    DELETE = auto()
    LIST_RECORDS = auto()

    @property
    def method_name(self) -> str:
        return self.name.lower()


@runtime_checkable
class EngineProtocol(Protocol):
    """Contract for memory engines."""

    @property
    def supported_operations(self) -> frozenset[Operation]:
        """Supported operations by this engine."""
        ...

    async def info(self) -> "InfoResponse":
        """Get knowledge base metadata.

        Returns engine type, record count, and configuration details.
        """
        ...

    async def query(self, query: str, top_k: int = 10) -> "QueryResponse":
        """Search the knowledge base.

        Args:
            query: Search text to find matching records.
            top_k: Maximum number of results to return.
        """
        ...

    async def insert(self, content: str, doc_id: str | None = None) -> "InsertResponse":
        """Add text content to the knowledge base.

        Args:
            content: Text content to store.
            doc_id: Optional custom ID. Auto-generated if not provided.
        """
        ...

    async def insert_file(
        self,
        file_path: str,
        content: str | None = None,
        doc_id: str | None = None,
    ) -> "InsertResponse":
        """Add a file to the knowledge base.

        Supports PDF, images, and other document formats depending on engine.

        Args:
            file_path: Local path to file, OR filename when content is provided.
            content: Base64-encoded file data. If provided, file_path is the filename.
            doc_id: Optional custom ID. Auto-generated if not provided.
        """
        ...

    async def delete(self, record_id: str) -> "DeleteResponse":
        """Remove a record from the knowledge base.

        Args:
            record_id: ID of the record to delete.
        """
        ...

    async def list_records(self, limit: int = 100, offset: int = 0) -> "ListResponse":
        """List records in the knowledge base.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip for pagination.
        """
        ...


# Validate at import: every Operation must have a matching method
for op in Operation:
    assert hasattr(EngineProtocol, op.method_name), (
        f"EngineProtocol is missing method for Operation.{op.name}"
    )
