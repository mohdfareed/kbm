"""Mem0 engine — AI-powered memory with automatic fact extraction.

Configuration reference: https://docs.mem0.ai/open-source/configuration
"""

__all__: list[str] = []

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any

from mem0 import AsyncMemory
from mem0.configs.base import MemoryConfig as Mem0MemoryConfig

from kbm import schema
from kbm.config import Engine, MemoryConfig

from .base import BaseEngine, Operation

logger = logging.getLogger(__name__)


class Mem0Engine(BaseEngine):
    """Mem0-backed engine with LLM fact extraction and semantic search.

    Text is processed by an LLM to extract structured memories with
    deduplication and conflict resolution.  Files are sent as
    multi-modal messages for vision-based extraction.
    """

    supported_operations = frozenset(
        {
            Operation.INFO,
            Operation.QUERY,
            Operation.INSERT,
            Operation.INSERT_FILE,
            Operation.DELETE,
            Operation.GET_RECORD,
            Operation.LIST_RECORDS,
        }
    )

    def __init__(self, memory: MemoryConfig) -> None:
        logger.info(f"Initializing {memory.engine} engine...")
        self._raw_config = memory.mem0.config

        config = {k: v for k, v in self._raw_config.items() if v is not None}
        self._mem0 = (
            AsyncMemory(config=Mem0MemoryConfig(**config)) if config else AsyncMemory()
        )

    # MARK: Protocol methods

    async def info(self) -> schema.InfoResponse:
        metadata: dict[str, str] = {}

        if self._raw_config.get("graph_store"):
            metadata["graph_store"] = self._raw_config["graph_store"]["provider"]
        if self._raw_config.get("reranker"):
            model = self._raw_config["reranker"].get("config", {}).get("model", "")
            metadata["reranker"] = model or self._raw_config["reranker"]["provider"]

        llm_cfg = self._raw_config.get("llm", {}).get("config", {})
        has_vision = llm_cfg.get("enable_vision", False)

        features: list[str] = []
        if has_vision:
            features.append("multi-modal (image) support via insert_file")
        if self._raw_config.get("graph_store"):
            features.append("graph memory (entity-relationship extraction)")
        if self._raw_config.get("reranker"):
            features.append("reranker-enhanced search")

        instructions = (
            "Mem0 AI-powered memory engine with automatic fact extraction. "
            "Insert: text is processed by an LLM to extract structured memories "
            "with deduplication and conflict resolution. "
            "Query: use natural language questions - Mem0 performs semantic search "
            "over extracted memories and returns ranked results."
        )
        if features:
            instructions += " Features: " + ", ".join(features) + "."

        return schema.InfoResponse(
            engine=Engine.MEM0.value,
            records=0,  # record count is managed by MemoryTools
            metadata=metadata,
            instructions=instructions,
        )

    async def query(self, query: str, top_k: int = 100) -> schema.QueryResponse:
        search_kwargs: dict[str, Any] = {
            "query": query,
            "limit": top_k,
        }
        if self._raw_config.get("reranker"):
            search_kwargs["rerank"] = True

        result = await self._mem0.search(**search_kwargs)
        memories: list[dict[str, Any]] = result.get("results", [])

        results = [
            schema.QueryResult(
                id=mem.get("id"),
                content=mem.get("memory", ""),
                score=mem.get("score"),
                created_at=mem.get("created_at"),
            )
            for mem in memories
        ]
        return schema.QueryResponse(results=results, query=query, total=len(results))

    async def insert(self, content: str, record_id: str) -> str | None:
        """Send text to Mem0 for LLM-based fact extraction."""
        messages = [{"role": "user", "content": content}]
        await self._mem0.add(
            messages=messages,
            metadata={"canonical_id": record_id},
        )
        return "Inserted into Mem0 memory"

    async def insert_file(self, path: Path, record_id: str) -> str | None:
        """Send file as a multi-modal message to Mem0 for vision extraction."""
        data = path.read_bytes()
        b64_data = base64.b64encode(data).decode("utf-8")
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data_url = f"data:{mime_type};base64,{b64_data}"

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Remember this file: {path.name}"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        await self._mem0.add(
            messages=messages,
            metadata={"canonical_id": record_id},
        )
        return f"Ingested: {path.name}"

    async def delete(self, record_id: str) -> None:
        """Best-effort cleanup of Mem0 memories linked to this record."""
        try:
            all_memories = await self._mem0.get_all()
            memories: list[dict[str, Any]] = all_memories.get("results", [])
            for mem in memories:
                metadata = mem.get("metadata", {}) or {}
                if metadata.get("canonical_id") == record_id:
                    await self._mem0.delete(memory_id=mem["id"])
        except Exception as e:
            logger.warning(f"Mem0 cleanup failed for {record_id}: {e}")
