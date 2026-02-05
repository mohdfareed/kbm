"""Federation engine - aggregates queries across multiple sources."""

__all__ = ["FederationEngine"]

import asyncio
import logging
from pathlib import Path

from kbm.config import MemoryConfig
from kbm.engine import EngineProtocol, Operation
from kbm.engines import get_engine
from kbm.engines.mcp_client import MCPClientEngine
from kbm.models import (
    DeleteResponse,
    InfoResponse,
    InsertResponse,
    ListResponse,
    QueryResponse,
    QueryResult,
)


class FederationEngine(EngineProtocol):
    logger = logging.getLogger(__name__)

    def __init__(self, config: "MemoryConfig") -> None:
        self.logger.info("Initializing Federation engine...")
        self._sources: list[tuple[str, EngineProtocol]] = []

        # Load from memory names
        for name in config.federation.memories:
            sub_config = MemoryConfig.from_name(name)
            engine = get_engine(sub_config)
            self._sources.append((name, engine))

        # Load from config file paths
        for path_str in config.federation.configs:
            path = Path(path_str).expanduser().resolve()
            sub_config = MemoryConfig.from_config(path)
            engine = get_engine(sub_config)
            self._sources.append((sub_config.name, engine))

        # Load from remote MCP URLs
        for url in config.federation.remotes:
            engine = MCPClientEngine(url)
            self._sources.append((url, engine))

        self.logger.info(f"Federation engine loaded {len(self._sources)} sources.")

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset({Operation.INFO, Operation.QUERY})

    async def info(self) -> InfoResponse:
        total_records = 0
        metadata: dict[str, str] = {}

        for name, engine in self._sources:
            self.logger.debug(f"Fetching info from federated source: {name}")
            try:
                info = await engine.info()
                total_records += info.records
                metadata[name] = f"{info.engine} ({info.records} records)"
            except Exception as e:
                self.logger.error(f"Error fetching info from {name}: {e}")
                metadata[name] = "error"

        return InfoResponse(
            engine="federation",
            records=total_records,
            metadata=metadata,
        )

    async def query(self, query: str, top_k: int = 10) -> QueryResponse:
        self.logger.debug(f"Querying federated sources with query: {query}")
        tasks = [engine.query(query, top_k) for _, engine in self._sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[QueryResult] = []
        for (name, _), result in zip(self._sources, results):
            if isinstance(result, BaseException):
                self.logger.error(f"Error querying {name}: {result}")
            elif isinstance(result, QueryResponse):
                # Prefix IDs with source name for disambiguation
                for r in result.results:
                    all_results.append(
                        QueryResult(
                            id=f"{name}:{r.id}",
                            content=r.content,
                            created_at=r.created_at,
                            score=r.score,
                        )
                    )

        return QueryResponse(results=all_results, query=query, total=len(all_results))

    async def insert(self, content: str, doc_id: str | None = None) -> InsertResponse:
        raise NotImplementedError("Federation is read-only")

    async def insert_file(
        self, file_path: str, content: str | None = None, doc_id: str | None = None
    ) -> InsertResponse:
        raise NotImplementedError("Federation is read-only")

    async def delete(self, record_id: str) -> DeleteResponse:
        raise NotImplementedError("Federation is read-only")

    async def list_records(self, limit: int = 100, offset: int = 0) -> ListResponse:
        raise NotImplementedError("Federation is read-only")
