"""RAG-Anything engine — multi-modal RAG with knowledge graphs."""

__all__: list[str] = []

import asyncio
import logging
import os
import sysconfig
from collections.abc import Callable
from pathlib import Path
from typing import Any

import raganything
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc

from kbm import schema
from kbm.config import MemoryConfig, RAGAnythingConfig
from kbm.config.config import Engine

from .base import BaseEngine, Operation

# Ensure venv scripts/ is on PATH so RAGAnything can find the `mineru` CLI
# (needed when running inside isolated tool environments like `uv tool`).
_scripts_dir = sysconfig.get_path("scripts")
if _scripts_dir and _scripts_dir not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = _scripts_dir + os.pathsep + os.environ.get("PATH", "")

logger = logging.getLogger(__name__)


def resolve_provider(
    provider: RAGAnythingConfig.Provider,
) -> tuple[Callable[..., Any], Callable[..., Any]]:
    match provider:
        case RAGAnythingConfig.Provider.OPENAI:
            from lightrag.llm.openai import openai_complete_if_cache, openai_embed

            return openai_complete_if_cache, openai_embed.func

        case RAGAnythingConfig.Provider.AZURE:
            from lightrag.llm.azure_openai import (
                azure_openai_complete_if_cache,
                azure_openai_embed,
            )

            return azure_openai_complete_if_cache, azure_openai_embed.func

        case RAGAnythingConfig.Provider.ANTHROPIC:
            from lightrag.llm.anthropic import (
                anthropic_complete_if_cache,
                anthropic_embed,
            )

            return anthropic_complete_if_cache, anthropic_embed

        case _:
            raise ValueError(f"Unsupported provider: {provider}")


class RAGAnythingEngine(BaseEngine):
    """Multi-modal RAG engine with knowledge graphs.

    Text and files are parsed into entities and relationships in a
    knowledge graph.  Queries extract context and synthesize answers
    from multiple sources rather than returning raw documents.
    """

    supported_operations = frozenset(
        {
            Operation.INFO,
            Operation.QUERY,
            Operation.INSERT,
            Operation.INSERT_FILE,
            Operation.GET_RECORD,
            Operation.LIST_RECORDS,
        }
    )  # no DELETE — cannot remove from knowledge graph

    def __init__(self, memory: MemoryConfig) -> None:
        logger.info(f"Initializing {memory.engine} engine...")
        self.config = memory.rag_anything
        self.working_dir = memory.settings.data_path / "rag_anything"
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self._api_key = self.config.api_key
        self._complete_func, self._embed_func = resolve_provider(self.config.provider)

        self._lightrag: LightRAG | None = None
        self._rag: raganything.RAGAnything | None = None
        self._rag_lock = asyncio.Lock()  # serialize RAG pipeline operations

    # MARK: Protocol methods

    async def info(self) -> schema.InfoResponse:
        return schema.InfoResponse(
            engine=Engine.RAG_ANYTHING.value,
            records=0,  # record count is managed by MemoryTools
            metadata={
                "query_mode": self.config.query_mode,
                "llm_model": self.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "embedding_dim": str(self.config.embedding_dim),
            },
            instructions=(
                "RAG engine (RAG-Anything) with knowledge graphs and semantic search. "
                f"Mode: '{self.config.query_mode}'. "
                "Insert: text and files are parsed into entities and relationships. "
                "Query: use natural language questions - the system extracts "
                "context and synthesizes answers from multiple sources rather "
                "than returning raw documents."
            ),
        )

    async def query(self, query: str, top_k: int = 1) -> schema.QueryResponse:
        rag = self._get_rag(await self._get_lightrag())
        result = await rag.aquery_vlm_enhanced(query, mode=self.config.query_mode)

        return schema.QueryResponse(
            results=[schema.QueryResult(content=str(result))] if result else [],
            query=query,
            total=1 if result else 0,
        )

    async def insert(self, content: str, record_id: str) -> str | None:
        """Index text content into the RAG knowledge graph."""
        async with self._rag_lock:
            rag = self._get_rag(await self._get_lightrag())
            await rag.insert_content_list(
                content_list=[{"type": "text", "text": content, "page_idx": 0}],
                file_path="text_insert.txt",
                doc_id=record_id,
            )
        return "Inserted into knowledge graph"

    async def insert_file(self, path: Path, record_id: str) -> str | None:
        """Ingest a file into the RAG pipeline."""
        async with self._rag_lock:
            rag = self._get_rag(await self._get_lightrag())
            await rag.process_document_complete(
                file_path=str(path),
                output_dir=str(self.working_dir / "output"),
                formula=False,  # FIXME: MinerU/transformers incompatibility bug
            )
        return f"Ingested: {path.name}"

    async def delete(self, record_id: str) -> None:
        raise NotImplementedError("RAG-Anything engine does not support deletion")

    # MARK: Internal

    def _get_rag(self, lightrag: LightRAG) -> raganything.RAGAnything:
        if self._rag is None:
            self._rag = raganything.RAGAnything(
                lightrag=lightrag,
                vision_model_func=self._vision_func,
                config=raganything.RAGAnythingConfig(
                    working_dir=str(self.working_dir),
                    parser_output_dir=str(self.working_dir / "output"),
                ),
            )
        return self._rag

    async def _get_lightrag(self) -> LightRAG:
        if self._lightrag is None:
            # Wrap bound methods in lambdas so LightRAG's
            # `asdict(self)` → `deepcopy` doesn't traverse into the
            # engine instance (which holds an unpicklable CanonStore).
            # `deepcopy` treats `FunctionType` (lambdas) as atomic but
            # follows `MethodType` (bound methods) into `__self__`.
            self._lightrag = LightRAG(
                working_dir=str(self.working_dir),
                embedding_func=self._get_embedding_func(),
                llm_model_func=lambda prompt, **kw: self._llm_func(prompt, **kw),
            )
        return self._lightrag

    def _get_embedding_func(self) -> EmbeddingFunc:
        return EmbeddingFunc(
            embedding_dim=self.config.embedding_dim,
            func=lambda texts: self._embed_func(
                texts,
                model=self.config.embedding_model,
                api_key=self._api_key,
                **self.config.config,
            ),
        )

    async def _llm_func(self, prompt: str, **kwargs) -> str:  # type: ignore[return]
        return await self._complete_func(
            model=self.config.llm_model,
            prompt=prompt,
            api_key=self._api_key,
            **self.config.config,
            **kwargs,
        )

    async def _vision_func(
        self,
        prompt: str,
        *,
        image_data: str | None = None,
        system_prompt: str | None = None,
        **kwargs,
    ) -> str:
        """Vision completion for multi-modal RAG."""
        content: str | list[dict] = prompt
        if image_data:
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}",
                    },
                },
            ]

        return await self._complete_func(
            model=self.config.vision_model,
            prompt=content,  # type: ignore[arg-type]
            system_prompt=system_prompt,
            api_key=self._api_key,
            **self.config.config,
            **kwargs,
        )
