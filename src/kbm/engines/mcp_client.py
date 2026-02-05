"""MCP client engine - connects to remote MCP servers.

This is used by federation engines to query remote memories.
"""

__all__ = ["MCPClientEngine"]

import logging
from datetime import datetime

from fastmcp import Client

from kbm.engine import EngineProtocol, Operation
from kbm.models import (
    DeleteResponse,
    InfoResponse,
    InsertResponse,
    ListResponse,
    QueryResponse,
    QueryResult,
)


class MCPClientEngine(EngineProtocol):
    logger = logging.getLogger(__name__)

    def __init__(self, url: str) -> None:
        self.logger.info(f"Initializing MCP client at: {url}")
        self._url = url
        self._client = Client(self._url)

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset({Operation.INFO, Operation.QUERY})

    async def info(self) -> InfoResponse:
        async with self._client:
            self.logger.debug(f"Fetching info from remote MCP server: {self._url}")
            result = await self._client.call_tool(Operation.INFO.method_name)

            # Try to parse structured response, fallback to basic
            if isinstance(result.data, dict):
                return InfoResponse(**result.data)

            self.logger.warning(
                "Received unstructured info response from remote MCP server: "
                f"{self._url}"
            )

            return InfoResponse(
                engine="remote",
                records=0,
                metadata={"url": self._url, "raw": str(result.data)},
            )

    async def query(self, query: str, top_k: int = 10) -> QueryResponse:
        async with self._client:
            self.logger.debug(f"Querying remote MCP server: {self._url}")
            result = await self._client.call_tool(
                Operation.QUERY.method_name, {"query": query, "top_k": top_k}
            )

            # Try to parse structured response, fallback to raw
            if isinstance(result.data, dict) and "results" in result.data:
                return QueryResponse(**result.data)

            self.logger.warning(
                "Received unstructured query response from remote MCP server: "
                f"{self._url}"
            )

            return QueryResponse(
                results=[
                    QueryResult(
                        id="remote",
                        content=str(result.data) if result.data else "",
                        created_at=datetime.now(),
                    )
                ]
                if result.data
                else [],
                query=query,
                total=1 if result.data else 0,
            )

    async def insert(self, content: str, doc_id: str | None = None) -> InsertResponse:
        raise NotImplementedError("Remote insert not supported")

    async def insert_file(
        self, file_path: str, content: str | None = None, doc_id: str | None = None
    ) -> InsertResponse:
        raise NotImplementedError("Remote insert_file not supported")

    async def delete(self, record_id: str) -> DeleteResponse:
        raise NotImplementedError("Remote delete not supported")

    async def list_records(self, limit: int = 100, offset: int = 0) -> ListResponse:
        raise NotImplementedError("Remote list_records not supported")
