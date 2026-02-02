"""Engine protocol and operation definitions."""

__all__ = ["EngineProtocol", "Operation"]

from enum import Enum, auto
from typing import Protocol, runtime_checkable


class Operation(Enum):
    """Operations that engines can support.

    All engines must support INFO and QUERY.
    Other operations are optional and declared via supported_operations.
    """

    INFO = auto()
    QUERY = auto()
    INSERT = auto()
    INSERT_FILE = auto()
    DELETE = auto()
    LIST_RECORDS = auto()

    @property
    def method_name(self) -> str:
        """Get the corresponding method name for this operation."""
        return self.name.lower()


# Required operations that all engines must support
REQUIRED_OPERATIONS: frozenset[Operation] = frozenset({Operation.INFO, Operation.QUERY})

# Optional operations that engines may support
OPTIONAL_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.INSERT,
        Operation.INSERT_FILE,
        Operation.DELETE,
        Operation.LIST_RECORDS,
    }
)


@runtime_checkable
class EngineProtocol(Protocol):
    """Contract all memory engines must fulfill.

    Engines implement this protocol and declare which operations they support
    via the `supported_operations` property. The server only registers tools
    for supported operations-models never see tools that would fail.

    All engines must support:
        - info(): Returns engine metadata
        - query(): Search/retrieve from memory

    Optional operations (declared via supported_operations):
        - insert: Add text content
        - insert_file: Parse and add a file
        - delete: Remove a record
        - list_records: List all records
    """

    @property
    def supported_operations(self) -> frozenset[Operation]:
        """Declare which operations this engine supports.

        Must include at minimum: {Operation.INFO, Operation.QUERY}.
        May also include: INSERT, INSERT_FILE, DELETE, LIST_RECORDS.
        """
        ...

    async def info(self) -> str:
        """Get information about the knowledge base."""
        ...

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information.

        Args:
            query: The search query.
            top_k: Maximum number of results to return.

        Returns:
            Formatted string with matching records.
        """
        ...

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert text content into the knowledge base.

        Args:
            content: The text content to insert.
            doc_id: Optional custom document ID (auto-generated if not provided).

        Returns:
            Confirmation message with the record ID.
        """
        ...

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Insert a file into the knowledge base (PDF, image, etc.).

        Args:
            file_path: Path to the file to insert.
            doc_id: Optional custom document ID (auto-generated if not provided).

        Returns:
            Confirmation message with the record ID.
        """
        ...

    async def delete(self, record_id: str) -> str:
        """Delete a record from the knowledge base by its ID.

        Args:
            record_id: The ID of the record to delete.

        Returns:
            Confirmation message.
        """
        ...

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """List records in the knowledge base.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            Formatted string with record IDs and metadata.
        """
        ...
