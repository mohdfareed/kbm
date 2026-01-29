"""CLI commands for RAG-Anything engine."""

__all__ = ["app"]

import asyncio
from typing import Annotated, Literal

import typer

from engines.rag_anything import get_engine

app = typer.Typer(
    name="memory", help="Knowledge base memory operations (RAG-Anything)."
)


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
) -> None:
    """Query the knowledge base."""
    engine = get_engine()
    result = asyncio.run(engine.query(query, mode=mode))
    typer.echo(result)


@app.command()
def insert(
    content: Annotated[str, typer.Argument(help="Text content to insert")],
    doc_id: Annotated[
        str | None, typer.Option(help="Custom document ID")
    ] = None,
) -> None:
    """Insert text content into the knowledge base."""
    engine = get_engine()
    result = asyncio.run(engine.insert(content, doc_id=doc_id))
    typer.echo(f"Created record: {result}")


@app.command()
def insert_file(
    file_path: Annotated[str, typer.Argument(help="Path to file to insert")],
    doc_id: Annotated[
        str | None, typer.Option(help="Custom document ID")
    ] = None,
) -> None:
    """Insert a file into the knowledge base."""
    engine = get_engine()
    result = asyncio.run(engine.insert_file(file_path, doc_id=doc_id))
    typer.echo(f"Created record: {result}")


@app.command()
def delete(
    record_id: Annotated[str, typer.Argument(help="ID of record to delete")],
) -> None:
    """Delete a record from the knowledge base."""
    engine = get_engine()
    asyncio.run(engine.delete(record_id))
    typer.echo(f"Deleted: {record_id}")


@app.command("list")
def list_records(
    limit: Annotated[
        int, typer.Option(help="Maximum records to return")
    ] = 100,
    offset: Annotated[int, typer.Option(help="Records to skip")] = 0,
) -> None:
    """List records in the knowledge base."""
    engine = get_engine()
    result = asyncio.run(engine.list_records(limit=limit, offset=offset))

    if not result:
        typer.echo("No records found.")
        return

    for record in result:
        typer.echo(record)


@app.command()
def info() -> None:
    """Get information about the knowledge base."""
    engine = get_engine()
    result = asyncio.run(engine.info())

    for key, value in result.items():
        typer.echo(f"{key}: {value}")
