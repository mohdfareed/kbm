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
        """Get information about the knowledge base."""
        ...

    async def query(self, query: str, top_k: int = 10) -> "QueryResponse":
        """Search the knowledge base for relevant information."""
        ...

    async def insert(self, content: str, doc_id: str | None = None) -> "InsertResponse":
        """Insert content into the knowledge base."""
        ...

    async def insert_file(
        self, file_path: str, doc_id: str | None = None
    ) -> "InsertResponse":
        """Insert content from a file into the knowledge base."""
        ...

    async def delete(self, record_id: str) -> "DeleteResponse":
        """Delete a record from the knowledge base."""
        ...

    async def list_records(self, limit: int = 100, offset: int = 0) -> "ListResponse":
        """List records in the knowledge base."""
        ...


# Validate at import: every Operation must have a matching method
for op in Operation:
    assert hasattr(EngineProtocol, op.method_name), (
        f"EngineProtocol is missing method for Operation.{op.name}"
    )
