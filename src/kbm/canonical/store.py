"""Async canonical store."""

__all__ = ["CanonicalStore"]

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kbm.canonical.models import Attachment, Base, Record


class CanonicalStore:
    """Async database storage for records and attachments."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url
        if self._url.startswith("sqlite"):
            # Extract path from sqlite+aiosqlite:///path/to/db
            path = self._url.split("///", 1)[-1]
            Path(path).parent.mkdir(parents=True, exist_ok=True)

        self._initialized = False
        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self._initialized:
            return

        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def close(self) -> None:
        """Close database connection."""
        await self._engine.dispose()

    async def _ensure_tables(self) -> None:
        if not self._initialized:
            await self.initialize()

    async def insert_record(
        self,
        content: str,
        doc_id: str | None = None,
        content_type: str = "text",
        source: str | None = None,
        metadata: str | None = None,
    ) -> str:
        """Insert a record, return its ID."""
        await self._ensure_tables()
        rid = doc_id or str(uuid.uuid4())

        async with self._session_factory() as session:
            record = Record(
                id=rid,
                content=content,
                content_type=content_type,
                source=source,
                metadata_json=metadata,
            )

            session.add(record)
            await session.commit()

        return rid

    async def get_record(self, record_id: str) -> Record | None:
        """Get a record by ID."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            return await session.get(Record, record_id)

    async def delete_record(self, record_id: str) -> bool:
        """Delete a record by ID."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            record = await session.get(Record, record_id)
            if record is None:
                return False

            await session.delete(record)
            await session.commit()
            return True

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[Record]:
        """List records with pagination."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            stmt = (
                select(Record)
                .order_by(Record.created_at.desc())
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_records(self) -> int:
        """Count total records."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            stmt = select(func.count()).select_from(Record)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def search_records(self, query: str, limit: int = 10) -> list[Record]:
        """Simple text search in content."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            stmt = select(Record).where(Record.content.contains(query)).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def insert_attachment(
        self,
        record_id: str,
        file_name: str,
        file_path: str,
        mime_type: str | None = None,
        size_bytes: int | None = None,
    ) -> str:
        """Insert an attachment for a record."""
        await self._ensure_tables()
        aid = str(uuid.uuid4())

        async with self._session_factory() as session:
            attachment = Attachment(
                id=aid,
                record_id=record_id,
                file_name=file_name,
                file_path=file_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
            )

            session.add(attachment)
            await session.commit()

        return aid

    async def get_attachments(self, record_id: str) -> list[Attachment]:
        """Get all attachments for a record."""
        await self._ensure_tables()
        async with self._session_factory() as session:
            stmt = select(Attachment).where(Attachment.record_id == record_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())
