"""Canonical data store — SQLite source of truth for all records."""

import base64
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base, ContentType, Record


class CanonicalStore:
    """Async SQLite storage for canonical records and file attachments."""

    def __init__(self, db_url: str, attachments_path: Path) -> None:
        self._engine = create_async_engine(db_url, echo=False)
        self._attachments = attachments_path
        self._ready = False
        self._sessions = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self) -> None:
        """Create tables if needed. Idempotent."""
        if self._ready:
            return
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._ready = True

    async def close(self) -> None:
        """Dispose the database engine."""
        await self._engine.dispose()

    # MARK: Record CRUD

    async def insert_record(
        self,
        content: str,
        doc_id: str | None = None,
        content_type: ContentType = ContentType.TEXT,
        source: str | None = None,
    ) -> str:
        """Insert a record, return its ID."""
        await self._ensure_ready()
        rid = doc_id or str(uuid.uuid4())
        async with self._sessions() as s:
            s.add(
                Record(
                    id=rid,
                    content=content,
                    content_type=content_type.value,
                    source=source,
                )
            )
            await s.commit()
        return rid

    async def get_record(self, record_id: str) -> Record | None:
        """Get a record by ID."""
        await self._ensure_ready()
        async with self._sessions() as s:
            return await s.get(Record, record_id)

    async def delete_record(self, record_id: str) -> bool:
        """Delete a record by ID. Returns whether it existed."""
        await self._ensure_ready()
        async with self._sessions() as s:
            record = await s.get(Record, record_id)
            if record is None:
                return False
            await s.delete(record)
            await s.commit()
            return True

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[Record]:
        """List records, newest first."""
        await self._ensure_ready()
        async with self._sessions() as s:
            stmt = (
                select(Record)
                .order_by(Record.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return list((await s.execute(stmt)).scalars().all())

    async def count_records(self) -> int:
        """Total record count."""
        await self._ensure_ready()
        async with self._sessions() as s:
            return (
                await s.execute(select(func.count()).select_from(Record))
            ).scalar() or 0

    async def search_records(self, query: str, limit: int = 10) -> list[Record]:
        """Substring search in content and source."""
        await self._ensure_ready()
        async with self._sessions() as s:
            stmt = (
                select(Record)
                .where(
                    or_(
                        Record.content.contains(query),
                        Record.source.contains(query),
                    )
                )
                .limit(limit)
            )
            return list((await s.execute(stmt)).scalars().all())

    # MARK: File Handling

    async def insert_file(
        self,
        file_path: str,
        content: str | None = None,
        doc_id: str | None = None,
    ) -> tuple[str, Path]:
        """Insert a file record, copying into attachments/ (content-deduped)."""
        abs_path = self._save_attachment(file_path, content)
        rel_path = str(abs_path.relative_to(self._attachments))

        rid = await self.insert_record(
            content=rel_path,
            doc_id=doc_id,
            content_type=ContentType.FILE,
            source=file_path,
        )
        return rid, abs_path

    # MARK: Private

    async def _ensure_ready(self) -> None:
        if not self._ready:
            await self.initialize()

    def _save_attachment(self, file_path: str, content: str | None) -> Path:
        """Decode or read file data, save content-deduped into attachments/.

        If `content` is provided, it's a base64-encoded string of the file bytes.
        Otherwise, `file_path` is treated as a path on disk to read the bytes
        from (used for local file inserts).
        """
        if content:  # Base64-encoded file content
            data, name = base64.b64decode(content), file_path

        else:  # Local file path
            src = Path(file_path)
            if not src.is_absolute():
                raise ValueError(f"Expected absolute path, got: {file_path}")
            if not src.is_file():
                raise FileNotFoundError(f"File not found: {file_path}")
            data, name = src.read_bytes(), src.name

        self._attachments.mkdir(parents=True, exist_ok=True)
        content_hash = hashlib.sha256(data).hexdigest()[:16]
        dest = self._attachments / f"{content_hash}-{Path(name).suffix}"

        if not dest.exists():
            dest.write_bytes(data)
        return dest
