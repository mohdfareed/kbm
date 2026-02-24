"""Markdown engine — portable, git-friendly memory stored as .md files.

Each record is a Markdown file with YAML frontmatter (id, created_at).
Queries use the canonical store's FTS5 full-text search.  The .md files
are a human-readable, committable mirror of the canonical data.
"""

__all__: list[str] = []

import logging
from datetime import datetime
from pathlib import Path

import yaml

from kbm import schema
from kbm.config import Engine, MemoryConfig
from kbm.store import CanonStore

from .base import BaseEngine, Operation

logger = logging.getLogger(__name__)

# MARK: Constants

_FRONTMATTER_SEP = "---"


# MARK: Engine


class MarkdownEngine(BaseEngine):
    """Markdown-file engine backed by canonical store FTS5.

    Records are written as individual ``.md`` files with YAML frontmatter
    into ``<data_path>/markdown/``.  Search delegates to the canonical
    store's FTS5 index (populated automatically by SQLite triggers).
    """

    supported_operations = frozenset(
        {
            Operation.INFO,
            Operation.QUERY,
            Operation.INSERT,
            Operation.DELETE,
            Operation.GET_RECORD,
            Operation.LIST_RECORDS,
        }
    )  # text-only, no file support

    def __init__(self, memory: MemoryConfig, store: CanonStore) -> None:
        logger.info(f"Initializing {memory.engine} engine...")
        self._store = store
        self._md_dir = memory.settings.data_path / "markdown"
        self._md_dir.mkdir(parents=True, exist_ok=True)

    # MARK: BaseEngine interface

    async def info(self) -> schema.InfoResponse:
        count = await self._store.count_records()
        return schema.InfoResponse(
            engine=Engine.MARKDOWN.value,
            records=count,
            instructions=(
                "Markdown-file engine with FTS5 search. "
                "Records are stored as .md files with YAML frontmatter, "
                "designed to be committed alongside code. "
                "Queries support tokenized word matching, prefix search, and "
                "phrase queries. Results are ranked by BM25 relevance. "
                "To edit a record, delete it and re-insert with updated content."
            ),
        )

    async def query(self, query: str, top_k: int = 10) -> schema.QueryResponse:
        records = await self._store.search_records(query, top_k)
        results = [
            schema.QueryResult(id=r.id, content=r.content, created_at=r.created_at)
            for r in records
        ]
        return schema.QueryResponse(results=results, query=query, total=len(results))

    async def insert(self, content: str, record_id: str) -> str | None:
        record = await self._store.get_record(record_id)
        created_at = record.created_at if record else datetime.now()
        self._write_md(record_id, content, created_at)
        return None

    async def insert_file(self, path: Path, record_id: str) -> str | None:
        return None  # text-only engine

    async def delete(self, record_id: str) -> None:
        md_path = self._md_path(record_id)
        if md_path.exists():
            md_path.unlink()
            logger.debug(f"Removed markdown file: {md_path.name}")

    # MARK: Helpers

    def _md_path(self, record_id: str) -> Path:
        """Return the path for a record's markdown file."""
        return self._md_dir / f"{record_id}.md"

    def _write_md(self, record_id: str, content: str, created_at: datetime) -> None:
        """Write a record as a markdown file with YAML frontmatter."""
        frontmatter = {
            "id": record_id,
            "created_at": created_at.isoformat(),
        }
        lines = [
            _FRONTMATTER_SEP,
            yaml.dump(frontmatter, default_flow_style=False).strip(),
            _FRONTMATTER_SEP,
            "",
            content,
            "",  # trailing newline
        ]
        self._md_path(record_id).write_text("\n".join(lines))
