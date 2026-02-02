"""RAG-Anything engine - multi-modal RAG with knowledge graphs."""

__all__ = ["RAGAnythingEngine"]

import os
from pathlib import Path

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from app import EngineProtocol, Operation, get_settings


class RAGAnythingEngine(EngineProtocol):
    """Multi-modal RAG engine with knowledge graphs powered by RAG-Anything.

    Supports semantic search across ingested documents using knowledge graphs.
    Does not support delete or list operations due to knowledge graph architecture.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.rag_anything
        self.working_dir = settings.engine_data_dir

        # Get API credentials (env vars take precedence)
        self._api_key = os.environ.get("OPENAI_API_KEY", self.config.api_key)
        self._base_url = os.environ.get("OPENAI_BASE_URL", self.config.base_url)

        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or "
                "rag_anything.api_key in config."
            )

        # Lazy-init instances
        self._lightrag: LightRAG | None = None
        self._rag: RAGAnything | None = None

    @property
    def supported_operations(self) -> frozenset[Operation]:
        """RAG-Anything supports insert and query only."""
        return frozenset(
            {
                Operation.INFO,
                Operation.QUERY,
                Operation.INSERT,
                Operation.INSERT_FILE,
            }
        )

    async def info(self) -> str:
        """Get information about the knowledge base."""
        return (
            f"Engine: rag-anything\n"
            f"Working directory: {self.working_dir}\n"
            f"LLM model: {self.config.llm_model}\n"
            f"Embedding model: {self.config.embedding_model}\n"
            f"Query mode: {self.config.query_mode}"
        )

    async def query(self, query: str, top_k: int = 10) -> str:
        """Search the knowledge base for relevant information."""
        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)
        return await rag.aquery(query, mode=self.config.query_mode)

    async def insert(self, content: str, doc_id: str | None = None) -> str:
        """Insert text content into the knowledge base."""
        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)

        content_list = [{"type": "text", "text": content, "page_idx": 0}]

        await rag.insert_content_list(
            content_list=content_list,
            file_path="text_insert.txt",
            doc_id=doc_id,
        )
        return "Content inserted into knowledge graph."

    async def insert_file(self, file_path: str, doc_id: str | None = None) -> str:
        """Insert a file into the knowledge base (PDF, image, etc.)."""
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)

        await rag.process_document_complete(
            file_path=str(path),
            output_dir=str(self.working_dir / "output"),
        )
        return f"File ingested into knowledge graph: {path.name}"

    async def delete(self, record_id: str) -> str:
        raise NotImplementedError

    async def list_records(self, limit: int = 100, offset: int = 0) -> str:
        raise NotImplementedError

    # Internal methods

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

    async def _get_lightrag(self) -> LightRAG:
        if self._lightrag is not None:
            return self._lightrag

        async def llm_model_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list | None = None,
            **kwargs,
        ) -> str:
            return await openai_complete_if_cache(
                self.config.llm_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages or [],
                api_key=self._api_key,
                base_url=self._base_url,
                **kwargs,
            )

        self._lightrag = LightRAG(
            working_dir=str(self.working_dir),
            llm_model_func=llm_model_func,
            embedding_func=self._get_embedding_func(),
        )
        await self._lightrag.initialize_storages()
        return self._lightrag

    def _get_rag(self, lightrag: LightRAG) -> RAGAnything:
        if self._rag is not None:
            return self._rag

        config = RAGAnythingConfig(
            working_dir=str(self.working_dir),
            enable_image_processing=self.config.enable_image_processing,
            enable_table_processing=self.config.enable_table_processing,
            enable_equation_processing=self.config.enable_equation_processing,
        )

        self._rag = RAGAnything(
            lightrag=lightrag,
            config=config,
        )
        return self._rag
