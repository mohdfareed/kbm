"""Mem0 engine - AI-powered memory with automatic fact extraction.

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

from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from . import schema
from .base_engine import EngineBase, Operation


class Mem0Engine(EngineBase):
    logger = logging.getLogger(__name__)
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

    def __init__(self, memory: MemoryConfig, store: CanonStore) -> None:
        super().__init__(memory, store)
        self._raw_config = memory.mem0.config

        config = {k: v for k, v in self._raw_config.items() if v is not None}
        self._mem0 = (
            AsyncMemory(config=Mem0MemoryConfig(**config)) if config else AsyncMemory()
        )

    # MARK: Hook overrides

    async def _info(self) -> schema.InfoResponse:
        count = await self._store.count_records()
        cfg = self._raw_config
        metadata: dict[str, str] = {}

        if cfg.get("graph_store"):
            metadata["graph_store"] = cfg["graph_store"]["provider"]
        if cfg.get("reranker"):
            model = cfg["reranker"].get("config", {}).get("model", "")
            metadata["reranker"] = model or cfg["reranker"]["provider"]

        llm_cfg = cfg.get("llm", {}).get("config", {})
        has_vision = llm_cfg.get("enable_vision", False)

        features: list[str] = []
        if has_vision:
            features.append("multi-modal (image) support via insert_file")
        if cfg.get("graph_store"):
            features.append("graph memory (entity-relationship extraction)")
        if cfg.get("reranker"):
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
            records=count,
            metadata=metadata,
            instructions=instructions,
        )

    async def _query(self, query: str, top_k: int = 100) -> schema.QueryResponse:
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

    async def _insert(
        self, content: str, doc_id: str | None = None
    ) -> schema.InsertResponse:
        """Store in canonical + add to Mem0 for fact extraction."""
        result = await super()._insert(content, doc_id)
        messages = [{"role": "user", "content": content}]

        await self._mem0.add(
            messages=messages,
            metadata={"canonical_id": result.id},
        )

        return schema.InsertResponse(id=result.id, message="Inserted into Mem0 memory")

    async def _insert_file(
        self,
        file_path: str,
        content: str | None = None,
        doc_id: str | None = None,
    ) -> schema.InsertResponse:
        """Store file in canonical + send as image message to Mem0."""
        result = await super()._insert_file(file_path, content, doc_id)

        # Build multi-modal message for Mem0
        if content:
            # Base64-encoded content provided directly
            b64_data = content
        else:
            # Read from local file
            data = Path(file_path).expanduser().resolve().read_bytes()
            b64_data = base64.b64encode(data).decode("utf-8")

        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        data_url = f"data:{mime_type};base64,{b64_data}"

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Remember this file: {file_path}"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]

        await self._mem0.add(
            messages=messages,
            metadata={"canonical_id": result.id},
        )

        return schema.InsertResponse(
            id=result.id, message=f"Ingested: {Path(file_path).name}"
        )

    async def _delete(self, record_id: str) -> schema.DeleteResponse:
        """Delete from canonical store and attempt cleanup in Mem0."""
        result = await super()._delete(record_id)
        # Best-effort cleanup of Mem0 memories linked to this record.
        # Mem0 manages its own memory IDs, so we search for related memories
        # and delete them by their Mem0 ID.
        try:
            all_memories = await self._mem0.get_all()
            memories: list[dict[str, Any]] = all_memories.get("results", [])
            for mem in memories:
                metadata = mem.get("metadata", {}) or {}
                if metadata.get("canonical_id") == record_id:
                    await self._mem0.delete(memory_id=mem["id"])
        except Exception as e:
            self.logger.warning(f"Mem0 cleanup failed for {record_id}: {e}")
        return result
