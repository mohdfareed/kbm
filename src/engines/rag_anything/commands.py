"""CLI commands for RAG-Anything engine."""

__all__ = ["app"]

import asyncio
from typing import Annotated, Literal

import typer

from engines.rag_anything import RAGAnythingEngine

app = typer.Typer(
    name="memory", help="Knowledge base memory operations (RAG-Anything)."
)

# Engine instance (initialized on first use)
_engine: RAGAnythingEngine | None = None


def _get_engine() -> RAGAnythingEngine:
    """Get or create the engine instance."""
    global _engine
    if _engine is None:
        _engine = RAGAnythingEngine()
    return _engine


@app.command()
def query(
    query: Annotated[str, typer.Argument(help="The query string")],
    mode: Annotated[
        Literal["local", "global", "hybrid", "naive", "mix"],
        typer.Option(
            help=(
                "Query mode: "
                "local=context-dependent, "
                "global=high-level themes, "
                "hybrid=both, "
                "naive=basic vector, "
                "mix=KG+vector+reranking"
            )
        ),
    ] = "hybrid",
    top_k: Annotated[
        int, typer.Option(help="Number of results to retrieve")
    ] = 60,
    only_context: Annotated[
        bool,
        typer.Option(
            "--only-context", help="Return only context without LLM response"
        ),
    ] = False,
) -> None:
    """Query the knowledge base."""
    engine = _get_engine()
    result = asyncio.run(
        engine.query(
            query,
            mode=mode,
            top_k=top_k,
            only_need_context=only_context,
        )
    )
    typer.echo(result)


@app.command()
def insert(
    content: Annotated[str, typer.Argument(help="Text content to insert")],
    doc_id: Annotated[
        str | None, typer.Option(help="Custom document ID")
    ] = None,
    split_by: Annotated[
        str | None, typer.Option(help="Character to split text by")
    ] = None,
) -> None:
    """Insert text content into the knowledge base."""
    engine = _get_engine()
    result = asyncio.run(
        engine.insert(
            content,
            doc_id=doc_id,
            split_by_character=split_by,
        )
    )
    typer.echo(f"Created record: {result}")


@app.command()
def insert_file(
    file_path: Annotated[str, typer.Argument(help="Path to file to insert")],
    doc_id: Annotated[
        str | None, typer.Option(help="Custom document ID")
    ] = None,
    parse_method: Annotated[
        Literal["auto", "ocr", "txt"],
        typer.Option(help="Parsing method"),
    ] = "auto",
    no_images: Annotated[
        bool, typer.Option("--no-images", help="Disable image processing")
    ] = False,
    no_tables: Annotated[
        bool, typer.Option("--no-tables", help="Disable table processing")
    ] = False,
    no_equations: Annotated[
        bool,
        typer.Option("--no-equations", help="Disable equation processing"),
    ] = False,
) -> None:
    """Insert a file into the knowledge base."""
    engine = _get_engine()
    result = asyncio.run(
        engine.insert_file(
            file_path,
            doc_id=doc_id,
            parse_method=parse_method,
            enable_image_processing=not no_images,
            enable_table_processing=not no_tables,
            enable_equation_processing=not no_equations,
        )
    )
    typer.echo(f"Created record: {result}")


@app.command()
def delete(
    record_id: Annotated[str, typer.Argument(help="ID of record to delete")],
    hard: Annotated[
        bool,
        typer.Option("--hard", help="Permanently delete (not soft delete)"),
    ] = False,
) -> None:
    """Delete a record from the knowledge base."""
    engine = _get_engine()
    asyncio.run(engine.delete(record_id))
    typer.echo(f"Deleted: {record_id}")


@app.command("list")
def list_records(
    include_deleted: Annotated[
        bool, typer.Option("--include-deleted", help="Include deleted records")
    ] = False,
    limit: Annotated[
        int, typer.Option(help="Maximum records to return")
    ] = 100,
    offset: Annotated[int, typer.Option(help="Records to skip")] = 0,
) -> None:
    """List records in the knowledge base."""
    engine = _get_engine()
    result = asyncio.run(
        engine.list_records(
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
    )

    if not result:
        typer.echo("No records found.")
        return

    for record in result:
        typer.echo(record)


@app.command()
def info() -> None:
    """Get information about the knowledge base."""
    engine = _get_engine()
    result = asyncio.run(engine.info())

    for key, value in result.items():
        typer.echo(f"{key}: {value}")
