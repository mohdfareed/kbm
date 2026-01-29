"""RAG-Anything engine - multimodal RAG with knowledge graphs."""

__all__ = ["RAGAnythingEngine", "get_engine"]

import os
from pathlib import Path
from typing import Any

from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from app.config import get_settings

_engine: "RAGAnythingEngine | None" = None


def get_engine() -> "RAGAnythingEngine":
    """Get or create the engine instance."""
    global _engine
    if _engine is None:
        _engine = RAGAnythingEngine()
    return _engine


class RAGAnythingEngine:
    """RAG-Anything engine wrapping multimodal RAG with knowledge graphs."""

    def __init__(self) -> None:
        """Initialize the RAG-Anything engine."""
        settings = get_settings()
        self.config = settings.rag_anything
        self.working_dir = settings.resolve_data_path(self.config.data_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Get API credentials (env vars take precedence)
        self._api_key = os.environ.get("OPENAI_API_KEY", self.config.api_key)
        self._base_url = os.environ.get(
            "OPENAI_BASE_URL", self.config.base_url
        )

        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or "
                "rag_anything.api_key in config."
            )

        # Lazy-init the RAGAnything instance
        self._rag: RAGAnything | None = None

    def _get_rag(self) -> RAGAnything:
        """Get or create the RAGAnything instance."""
        if self._rag is not None:
            return self._rag

        config = RAGAnythingConfig(
            working_dir=str(self.working_dir),
            enable_image_processing=self.config.enable_image_processing,
            enable_table_processing=self.config.enable_table_processing,
            enable_equation_processing=self.config.enable_equation_processing,
        )

        async def llm_model_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list | None = None,
            **kwargs: Any,
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

        embedding_func = EmbeddingFunc(
            embedding_dim=self.config.embedding_dim,
            max_token_size=8192,
            func=lambda texts: openai_embed(
                texts,
                model=self.config.embedding_model,
                api_key=self._api_key,
                base_url=self._base_url,
            ),
        )

        self._rag = RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
        )
        return self._rag

    # MARK: - Public methods

    async def query(self, query: str, **kwargs: Any) -> str:
        """Query the knowledge base.

        Kwargs:
            mode: Query mode (local/global/hybrid/naive/mix)
        """
        mode = kwargs.get("mode", "hybrid")
        rag = self._get_rag()
        return await rag.aquery(query, mode=mode)

    async def insert(self, content: str, **kwargs: Any) -> str:
        """Insert content into the knowledge base.

        Kwargs:
            doc_id: Custom document ID
        """
        doc_id = kwargs.get("doc_id")
        rag = self._get_rag()

        # Create a content list for insertion
        content_list = [{"type": "text", "text": content, "page_idx": 0}]

        await rag.insert_content_list(
            content_list=content_list,
            file_path="text_insert.txt",
            doc_id=doc_id,
        )
        return doc_id or "auto-generated"

    async def insert_file(self, file_path: str, **kwargs: Any) -> str:
        """Insert a file into the knowledge base.

        Kwargs:
            doc_id: Custom document ID
        """
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        rag = self._get_rag()

        # Use process_document_complete for full document processing
        await rag.process_document_complete(
            file_path=str(path),
            output_dir=str(self.working_dir / "output"),
        )
        return kwargs.get("doc_id") or path.stem

    async def delete(self, record_id: str) -> None:
        """Remove a record from the knowledge base.

        Note: RAG-Anything doesn't have a direct delete API.
        """
        raise NotImplementedError(
            "Delete is not supported by RAG-Anything. "
            "Remove the working_dir to reset."
        )

    async def list_records(self, **kwargs: Any) -> list[dict]:
        """List records in the knowledge base.

        Note: RAG-Anything uses knowledge graphs, not document lists.
        """
        raise NotImplementedError(
            "List records is not supported by RAG-Anything. "
            "Use query to search the knowledge base."
        )

    async def info(self) -> dict:
        """Get engine information."""
        return {
            "engine": "rag-anything",
            "working_dir": str(self.working_dir),
            "llm_model": self.config.llm_model,
            "embedding_model": self.config.embedding_model,
            "embedding_dim": self.config.embedding_dim,
            "enable_image_processing": self.config.enable_image_processing,
            "enable_table_processing": self.config.enable_table_processing,
            "enable_equation_processing": self.config.enable_equation_processing,
        }
