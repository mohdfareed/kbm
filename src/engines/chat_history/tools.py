"""MCP tools for history engine."""

__all__ = ["register"]

import asyncio
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from engines.chat_history import get_engine


def register(mcp: FastMCP) -> None:
    """Register chat history tools with the MCP server."""

    @mcp.tool
    def query(
        query: str,
        top_k: Annotated[
            int, Field(description="Maximum number of results to return")
        ] = 10,
    ) -> str:
        """Search the knowledge base for relevant information."""
        engine = get_engine()
        return asyncio.run(engine.query(query, top_k=top_k))

    @mcp.tool
    def insert(
        content: str,
        doc_id: Annotated[
            str | None,
            Field(
                description="""
                Optional custom document ID (auto-generated if not provided)
                """
            ),
        ] = None,
    ) -> str:
        """Insert text content into the knowledge base."""
        engine = get_engine()
        return asyncio.run(engine.insert(content, doc_id=doc_id))

    @mcp.tool
    def insert_file(
        file_path: str,
        doc_id: Annotated[
            str | None,
            Field(
                description="""
                Optional custom document ID (auto-generated if not provided)
                """
            ),
        ] = None,
    ) -> str:
        """Insert a file into the knowledge base (PDF, image, etc.)."""
        engine = get_engine()
        return asyncio.run(engine.insert_file(file_path, doc_id=doc_id))

    @mcp.tool
    def delete(record_id: str) -> str:
        """Delete a record from the knowledge base by its ID."""
        engine = get_engine()
        asyncio.run(engine.delete(record_id))
        return f"Deleted {record_id}"

    @mcp.tool
    def list_records(
        limit: Annotated[
            int, Field(description="Maximum number of records to return")
        ] = 100,
        offset: Annotated[int, Field(description="Number of records to skip")] = 0,
    ) -> list[dict]:
        """List records in the knowledge base."""
        engine = get_engine()
        return asyncio.run(engine.list_records(limit=limit, offset=offset))

    @mcp.tool
    def info() -> dict:
        """Get information about the knowledge base."""
        engine = get_engine()
        return asyncio.run(engine.info())
