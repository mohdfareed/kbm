"""MCP tools for RAG-Anything engine."""

__all__ = ["register"]

import asyncio
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from engines.rag_anything import RAGAnythingEngine

# Engine instance (initialized on first use)
_engine: RAGAnythingEngine | None = None


def _get_engine() -> RAGAnythingEngine:
    """Get or create the engine instance."""
    global _engine
    if _engine is None:
        _engine = RAGAnythingEngine()
    return _engine


def register(mcp: FastMCP) -> None:
    """Register RAG-Anything tools with the MCP server."""

    @mcp.tool
    def query(
        query: str,
        mode: Annotated[
            Literal["local", "global", "hybrid", "naive", "mix"],
            Field(
                description=(
                    "Query mode: "
                    "'local' for context-dependent info, "
                    "'global' for high-level themes, "
                    "'hybrid' combines both, "
                    "'naive' for basic vector search, "
                    "'mix' for KG + vector + reranking"
                )
            ),
        ] = "hybrid",
        top_k: Annotated[
            int,
            Field(
                description="Number of top entities/relationships to retrieve"
            ),
        ] = 60,
        only_need_context: Annotated[
            bool,
            Field(
                description="If true, return only retrieved context without LLM response"
            ),
        ] = False,
    ) -> str:
        """Query the knowledge base.

        Args:
            query: The query string.
            params: Query parameters.
        """
        engine = _get_engine()
        return asyncio.run(
            engine.query(
                query,
                mode=mode,
                top_k=top_k,
                only_need_context=only_need_context,
            )
        )

    @mcp.tool
    def insert(
        content: str,
        doc_id: Annotated[
            str | None,
            Field(
                description="Optional custom document ID (auto-generated if not provided)"
            ),
        ] = None,
        split_by_character: Annotated[
            str | None,
            Field(description="Optional character to split text by"),
        ] = None,
    ) -> str:
        """Insert text content into the knowledge base.

        Args:
            content: The text content to insert.
            params: Insert parameters (doc_id, split_by_character).
        """
        engine = _get_engine()
        return asyncio.run(
            engine.insert(
                content,
                doc_id=doc_id,
                split_by_character=split_by_character,
            )
        )

    @mcp.tool
    def insert_file(
        file_path: str,
        doc_id: Annotated[
            str | None,
            Field(
                description="Optional custom document ID (auto-generated if not provided)"
            ),
        ] = None,
        parse_method: Annotated[
            Literal["auto", "ocr", "txt"],
            Field(description="Parsing method: 'auto', 'ocr', or 'txt'"),
        ] = "auto",
        enable_image_processing: Annotated[
            bool, Field(description="Enable image extraction and analysis")
        ] = True,
        enable_table_processing: Annotated[
            bool, Field(description="Enable table extraction and analysis")
        ] = True,
        enable_equation_processing: Annotated[
            bool, Field(description="Enable equation/formula extraction")
        ] = True,
    ) -> str:
        """Insert a file into the knowledge base.

        Args:
            file_path: Path to the file to insert.
            params: Insert parameters (doc_id, parse_method, enable_*).
        """
        engine = _get_engine()
        return asyncio.run(
            engine.insert_file(
                file_path,
                doc_id=doc_id,
                parse_method=parse_method,
                enable_image_processing=enable_image_processing,
                enable_table_processing=enable_table_processing,
                enable_equation_processing=enable_equation_processing,
            )
        )

    @mcp.tool
    def delete(
        record_id: str,
        soft_delete: Annotated[
            bool,
            Field(
                description="If true, mark as deleted; if false, permanently remove"
            ),
        ] = True,
    ) -> str:
        """Delete a record from the knowledge base.

        Args:
            record_id: The ID of the record to delete.
            params: Delete parameters (soft_delete).
        """
        engine = _get_engine()
        asyncio.run(engine.delete(record_id))
        return f"Deleted {record_id}"

    @mcp.tool
    def list_records(
        include_deleted: Annotated[
            bool, Field(description="Include soft-deleted records in the list")
        ] = False,
        limit: Annotated[
            int, Field(description="Maximum number of records to return")
        ] = 100,
        offset: Annotated[
            int, Field(description="Number of records to skip")
        ] = 0,
    ) -> list[dict]:
        """List records in the knowledge base.

        Args:
            params: List parameters (include_deleted, limit, offset).
        """
        engine = _get_engine()
        return asyncio.run(
            engine.list_records(
                include_deleted=include_deleted,
                limit=limit,
                offset=offset,
            )
        )

    @mcp.tool
    def info() -> dict:
        """Get information about the knowledge base."""
        engine = _get_engine()
        return asyncio.run(engine.info())
