"""RAG-Anything engine - multi-modal RAG with knowledge graphs."""

__all__ = ["RAGAnythingEngine"]

import os
from pathlib import Path
from typing import TYPE_CHECKING

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from kbm.engine import EngineProtocol, Operation

if TYPE_CHECKING:
    from kbm.config import MemoryConfig


class RAGAnythingEngine(EngineProtocol):
    """Knowledge graph RAG. Does not support delete/list_records."""

    def __init__(self, config: "MemoryConfig") -> None:
        self.config = config.rag_anything
        self.working_dir = config.engine_data_path
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self._api_key = os.environ.get("OPENAI_API_KEY", self.config.api_key)
        self._base_url = os.environ.get("OPENAI_BASE_URL", self.config.base_url)
        if not self._api_key:
            raise ValueError("Set OPENAI_API_KEY or rag_anything.api_key")

        self._lightrag: LightRAG | None = None
        self._rag: RAGAnything | None = None

    @property
    def supported_operations(self) -> frozenset[Operation]:
        return frozenset(
            {Operation.INFO, Operation.QUERY, Operation.INSERT, Operation.INSERT_FILE}
        )

    async def info(self) -> str:
        """Get information about the knowledge base."""
        return (
            f"Engine: rag-anything\n"
            f"LLM: {self.config.llm_model}\n"
            f"Mode: {self.config.query_mode}"
        )

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information."""
        rag = self._get_rag(await self._get_lightrag())
        return await rag.aquery(query, mode=self.config.query_mode)

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert text content into the knowledge base."""
        rag = self._get_rag(await self._get_lightrag())
        await rag.insert_content_list(
            content_list=[{"type": "text", "text": content, "page_idx": 0}],
            file_path="text_insert.txt",
            doc_id=doc_id,
        )
        return "Inserted into knowledge graph."

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Insert a file into the knowledge base (PDF, image, etc.)."""
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        rag = self._get_rag(await self._get_lightrag())
        await rag.process_document_complete(
            file_path=str(path), output_dir=str(self.working_dir / "output")
        )
        return f"Ingested: {path.name}"

    async def delete(self, record_id: str) -> str:
        """Not supported by this engine."""
        raise NotImplementedError("RAG-Anything does not support delete.")

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        """Not supported by this engine."""
        raise NotImplementedError("RAG-Anything does not support list.")

    # --- Internal ---

    def _get_embedding_func(self) -> EmbeddingFunc:
        return EmbeddingFunc(
            embedding_dim=self.config.embedding_dim,
            max_token_size=8192,
            func=lambda texts: openai_embed.func(
                texts,
                model=self.config.embedding_model,
                api_key=self._api_key,
                base_url=self._base_url,
            ),
        )

    async def _llm_func(self, prompt: str, **kwargs) -> str:  # type: ignore[return]
        return await openai_complete_if_cache(
            model=self.config.llm_model,
            prompt=prompt,
            api_key=self._api_key,
            base_url=self._base_url,
            **kwargs,
        )

    async def _get_lightrag(self) -> LightRAG:
        if self._lightrag is None:
            self._lightrag = LightRAG(
                working_dir=str(self.working_dir),
                embedding_func=self._get_embedding_func(),
                llm_model_func=self._llm_func,
            )
        return self._lightrag

    def _get_rag(self, lightrag: LightRAG) -> RAGAnything:
        if self._rag is None:
            self._rag = RAGAnything(
                lightrag=lightrag,
                config=RAGAnythingConfig(
                    enable_image_processing=self.config.enable_image_processing,
                    enable_table_processing=self.config.enable_table_processing,
                    enable_equation_processing=self.config.enable_equation_processing,
                ),
            )
        return self._rag
