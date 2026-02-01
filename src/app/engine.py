"""Engine protocol and capability definitions."""

__all__ = ["CAPABILITY_METHODS", "REQUIRED_METHODS", "Capability", "EngineProtocol"]

from collections.abc import Callable
from enum import Flag, auto
from typing import Protocol, runtime_checkable


class Capability(Flag):
    """Optional features an engine may support.

    Engines declare capabilities via their `capabilities` property.
    Server/CLI only register operations for declared capabilities.

    Note: `info()` and `query()` are always required and not gated.
    """

    NONE = 0
    INSERT = auto()
    INSERT_FILE = auto()
    DELETE = auto()
    LIST = auto()


@runtime_checkable
class EngineProtocol(Protocol):
    """Contract all memory engines must fulfill.

    Engines implement this protocol and declare which capabilities
    they support. The server registers tools only for supported
    capabilities—models never see operations that would fail.

    Required:
        - capabilities: Declare supported operations
        - info(): Returns engine metadata
        - query(): Search/retrieve from memory
        - get_extra_tools(): Return engine-specific tools (can be empty)

    Optional (capability-gated):
        - insert(): Requires INSERT
        - insert_file(): Requires INSERT_FILE
        - delete(): Requires DELETE
        - list_records(): Requires LIST
    """

    @property
    def capabilities(self) -> Capability:
        """Declare which optional features this engine supports."""
        ...

    async def info(self) -> str:
        """Return engine/memory metadata. Always available."""
        ...

    async def query(self, query: str) -> str:
        """Retrieve relevant records. Always required."""
        ...

    async def insert(self, content: str) -> str:
        """Add text content. Requires INSERT capability."""
        ...

    async def insert_file(self, file_path: str) -> str:
        """Parse and add a file. Requires INSERT_FILE capability."""
        ...

    async def delete(self, record_id: str) -> str:
        """Remove a record. Requires DELETE capability."""
        ...

    async def list_records(self) -> str:
        """List all records. Requires LIST capability."""
        ...

    def get_extra_tools(self) -> list[Callable]:
        """Return engine-specific tools to register.

        Engines can expose additional features beyond the core protocol.
        Each callable should be an async function with a docstring.
        Returns empty list by default.
        """
        ...


# Method mappings - single source of truth for tool/command registration.
# Using actual method references ensures type checking and refactoring support.

REQUIRED_METHODS: list[Callable] = [
    EngineProtocol.info,
    EngineProtocol.query,
]

CAPABILITY_METHODS: dict[Capability, Callable] = {
    Capability.INSERT: EngineProtocol.insert,
    Capability.INSERT_FILE: EngineProtocol.insert_file,
    Capability.DELETE: EngineProtocol.delete,
    Capability.LIST: EngineProtocol.list_records,
}
