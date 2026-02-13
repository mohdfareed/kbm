"""Engine protocol — the interface every storage engine implements.

Engines handle *only* engine-specific logic (querying, indexing,
cleanup).  Canonical record storage and MCP tool registration live
in ``MemoryTools`` (see ``engines/tools.py``).
"""

__all__: list[str] = []

from enum import Enum, auto
from pathlib import Path
from typing import Protocol, runtime_checkable

from kbm import schema


class Operation(Enum):
    """Engine operations. Names match ``MemoryTools`` public method names."""

    INFO = auto()
    QUERY = auto()
    INSERT = auto()
    INSERT_FILE = auto()
    DELETE = auto()
    GET_RECORD = auto()
    LIST_RECORDS = auto()

    @property
    def method_name(self) -> str:
        return self.name.lower()


@runtime_checkable
class BaseEngine(Protocol):
    """Interface that every storage engine must satisfy.

    Engines receive *only* engine-specific calls:

    * ``info``  — return metadata about the engine.
    * ``query`` — search the engine's index.
    * ``insert`` / ``insert_file`` — react to a record that has
      *already* been written to the canonical store.
    * ``delete``  — clean up engine-specific data for a record that
      is *about to be* removed from the canonical store.

    The canonical store write is handled by ``MemoryTools``; engines
    never touch it directly (except ChatHistory, which reads it for
    full-text search).
    """

    supported_operations: frozenset[Operation]
    """Operations this engine exposes as MCP tools."""

    async def info(self) -> schema.InfoResponse:
        """Return engine metadata (type, record count, capabilities)."""
        ...

    async def query(self, query: str, top_k: int) -> schema.QueryResponse:
        """Search the engine's index and return matching results."""
        ...

    async def insert(self, content: str, record_id: str) -> str | None:
        """React to a newly inserted text record.

        Called *after* the canonical store write succeeds.
        Return an optional status message for the MCP response.
        """
        ...

    async def insert_file(self, path: Path, record_id: str) -> str | None:
        """React to a newly inserted file record.

        ``path`` is the resolved, on-disk attachment written by the
        canonical store — always a real file, never a filename stub.
        Return an optional status message for the MCP response.
        """
        ...

    async def delete(self, record_id: str) -> None:
        """Clean up engine-specific data before a record is deleted."""
        ...
