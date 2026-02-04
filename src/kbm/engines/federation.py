"""Federation engine - aggregates queries across multiple sources."""

__all__ = ["FederationEngine"]

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


class FederationEngine(EngineProtocol):
    """Queries multiple sources and combines results."""

    logger = logging.getLogger(__name__)

    def __init__(self, config: "MemoryConfig") -> None:
        self.logger.info("Initializing Federation engine...")
        from kbm.config import MemoryConfig
        from kbm.engines import get_engine
        from kbm.engines.mcp_client import MCPClientEngine

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

    async def info(self) -> str:
        """Get info from all federated sources."""
        lines = [f"Engine: federation ({len(self._sources)} sources)"]
        for name, engine in self._sources:
            self.logger.debug(f"Fetching info from federated source: {name}")

            try:
                info = await engine.info()
                lines.append(f"\n[{name}]\n{info}")
            except Exception as e:
                self.logger.error(f"Error fetching info from {name}: {e}")
                lines.append(f"\n[{name}] Failed to retrieve info.")

        return "\n".join(lines)

    async def query(self, query: str, top_k: int = 10) -> str:
        """Query all sources and combine results."""
        self.logger.debug(f"Querying federated sources with query: {query}")
        tasks = [engine.query(query, top_k) for _, engine in self._sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        lines = []
        for (name, _), result in zip(self._sources, results):
            if isinstance(result, BaseException):
                self.logger.error(f"Error querying {name}: {result}")
                lines.append(f"[{name}] Failed to query.")
            elif "No matching" not in result and result.strip():
                lines.append(f"[{name}]\n{result}")

        return "\n\n".join(lines) if lines else "No matching records found."

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        raise NotImplementedError("Federation is read-only")

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        raise NotImplementedError("Federation is read-only")

    async def delete(self, record_id: str) -> str:
        raise NotImplementedError("Federation is read-only")

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        raise NotImplementedError("Federation is read-only")
