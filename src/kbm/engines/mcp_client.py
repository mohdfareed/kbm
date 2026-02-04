"""MCP client engine - connects to remote MCP servers."""

__all__ = ["MCPClientEngine"]

from typing import TYPE_CHECKING

from fastmcp import Client

from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


class MCPClientEngine(EngineProtocol):
    """Wraps a remote MCP server as an engine."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = Client(self._url)

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset({Operation.INFO, Operation.QUERY})

    async def info(self) -> str:
        """Get info from remote server."""
        async with self._client:
            result = await self._client.call_tool(Operation.INFO.method_name)
            return str(result.data) if result.data else f"Remote: {self._url}"

    async def query(self, query: str, top_k: int = 10) -> str:
        """Query the remote server."""
        async with self._client:
            result = await self._client.call_tool(
                Operation.QUERY.method_name, {"query": query, "top_k": top_k}
            )
            return str(result.data) if result.data else "No results"

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        raise NotImplementedError("Remote insert not supported")

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        raise NotImplementedError("Remote insert_file not supported")

    async def delete(self, record_id: str) -> str:
        raise NotImplementedError("Remote delete not supported")

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        raise NotImplementedError("Remote list_records not supported")
