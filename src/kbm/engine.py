"""Engine protocol and operations."""

__all__ = ["EngineProtocol", "Operation"]

from enum import Enum, auto
from typing import Protocol, runtime_checkable


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
    def supported_operations(self) -> frozenset[Operation]: ...
    async def info(self) -> str: ...
    async def query(self, query: str, top_k: int = 10) -> str: ...
    async def insert(self, content: str, doc_id: str | None = None) -> str: ...
    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str: ...
    async def delete(self, record_id: str) -> str: ...
    async def list_records(self, limit: int = 100, offset: int = 0) -> str: ...


# Validate at import: every Operation must have a matching method
for op in Operation:
    assert hasattr(EngineProtocol, op.method_name), (
        f"EngineProtocol is missing method for Operation.{op.name}"
    )
