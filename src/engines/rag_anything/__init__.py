"""RAG-Anything engine - multi-modal RAG with knowledge graphs."""

__all__ = ["RAGAnythingEngine"]

import os
from collections.abc import Callable
from pathlib import Path

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from app.config import get_settings
from app.engine import Capability
from engines import register_engine


@register_engine("rag-anything")
class RAGAnythingEngine:
    """Multi-modal RAG engine with knowledge graphs powered by RAG-Anything.

    Supports semantic search across ingested documents using knowledge graphs.
    Does not support delete or list operations due to knowledge graph architecture.
    """

    def __init__(self) -> None:
        """Initialize the RAG-Anything engine."""
        settings = get_settings()
        self.config = settings.rag_anything
        self.working_dir = settings.resolve_data_path(self.config.data_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

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
    def capabilities(self) -> Capability:
        """RAG-Anything supports insert and file insertion."""
        return Capability.INSERT | Capability.INSERT_FILE

    # MARK: - Public methods

    async def info(self) -> str:
        """Get memory metadata including model configuration."""
        return (
            f"Engine: rag-anything\n"
            f"Working directory: {self.working_dir}\n"
            f"LLM model: {self.config.llm_model}\n"
            f"Embedding model: {self.config.embedding_model}"
        )

    async def query(self, query: str) -> str:
        """Search the knowledge graph using hybrid mode (local + global)."""
        return await self._query_with_mode(query, "hybrid")

    async def insert(self, content: str) -> str:
        """Add text content to the knowledge graph.

        Content is chunked, embedded, and linked into the knowledge graph
        for semantic retrieval.
        """
        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)

        content_list = [{"type": "text", "text": content, "page_idx": 0}]

        await rag.insert_content_list(
            content_list=content_list,
            file_path="text_insert.txt",
            doc_id=None,
        )
        return "Content inserted into knowledge graph"

    async def insert_file(self, file_path: str) -> str:
        """Parse and ingest a file (PDF, image, etc.) into the knowledge graph.

        Documents are processed with multimodal understanding and linked
        into the knowledge graph for semantic retrieval.
        """
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)

        await rag.process_document_complete(
            file_path=str(path),
            output_dir=str(self.working_dir / "output"),
        )
        return f"File ingested into knowledge graph: {path.name}"

    # MARK: - Engine-specific extras

    async def query_local(self, query: str) -> str:
        """Search using only local context (no graph traversal)."""
        return await self._query_with_mode(query, "local")

    async def query_global(self, query: str) -> str:
        """Search using global knowledge graph themes."""
        return await self._query_with_mode(query, "global")

    def get_extra_tools(self) -> list[Callable]:
        """Return query mode variants as extra tools."""
        return [self.query_local, self.query_global]

    # Note: delete() and list_records() not implemented - not in capabilities

    # MARK: - Private methods

    def _get_embedding_func(self) -> EmbeddingFunc:
        """Create the embedding function."""
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
        """Get or create the LightRAG instance (handles data loading)."""
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
        """Get or create the RAGAnything instance."""
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

    async def _query_with_mode(self, query: str, mode: str) -> str:
        """Internal: query with specific mode."""
        lightrag = await self._get_lightrag()
        rag = self._get_rag(lightrag)
        return await rag.aquery(query, mode=mode)
