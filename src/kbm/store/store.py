"""Async canonical store."""

__all__ = ["CanonicalStore"]

import base64
import hashlib
import logging
import uuid
from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kbm.store.models import Attachment, Base, Record


class CanonicalStore:
    """Async database storage for records and attachments."""

    logger = logging.getLogger(__name__)

    def __init__(self, database_url: str, uploads_path: Path | None = None) -> None:
        self.logger.info(f"Initializing CanonicalStore with URL: {database_url}")

        self._url = database_url
        self._uploads_path = uploads_path
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
            self.logger.debug("Creating database tables...")
            await connection.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def close(self) -> None:
        """Close database connection."""
        self.logger.debug("Disposing database engine...")
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
        self.logger.debug("Inserting new record into CanonicalStore...")

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
        self.logger.debug(f"Fetching record with ID: {record_id}")

        async with self._session_factory() as session:
            return await session.get(Record, record_id)

    async def delete_record(self, record_id: str) -> bool:
        """Delete a record by ID."""
        await self._ensure_tables()
        self.logger.debug(f"Deleting record with ID: {record_id}")

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
        self.logger.debug(f"Listing records with limit={limit}, offset={offset}")

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
        self.logger.debug("Counting total records in CanonicalStore...")

        async with self._session_factory() as session:
            stmt = select(func.count()).select_from(Record)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def search_records(self, query: str, limit: int = 10) -> list[Record]:
        """Text search in content and source (includes filenames for uploads)."""
        await self._ensure_tables()
        self.logger.debug(f"Searching records with query: {query}, limit: {limit}")

        async with self._session_factory() as session:
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
            result = await session.execute(stmt)
            return list(result.scalars().all())

    def _save_upload(self, filename: str, data: bytes) -> Path:
        """Save uploaded file to persistent storage, return path."""
        if not self._uploads_path:
            raise ValueError("uploads_path not configured")
        self._uploads_path.mkdir(parents=True, exist_ok=True)

        # Hash content for deduplication
        content_hash = hashlib.sha256(data).hexdigest()[:16]
        # Preserve extension for mime type detection
        ext = Path(filename).suffix
        safe_name = f"{content_hash}{ext}"
        path = self._uploads_path / safe_name

        # Only write if not already exists (deduplication)
        if not path.exists():
            path.write_bytes(data)
            self.logger.debug(f"Saved upload: {path}")
        else:
            self.logger.debug(f"Upload already exists: {path}")

        return path

    async def _insert_attachment(
        self,
        record_id: str,
        path: Path,
    ) -> str:
        """Insert an attachment record for a file."""
        await self._ensure_tables()
        self.logger.debug(f"Inserting attachment for record ID: {record_id}")

        aid = str(uuid.uuid4())
        async with self._session_factory() as session:
            attachment = Attachment(
                id=aid,
                record_id=record_id,
                file_name=path.name,
                file_path=str(path),
                mime_type=None,
                size_bytes=path.stat().st_size if path.exists() else None,
            )

            session.add(attachment)
            await session.commit()

        return aid

    def resolve_file(self, file_path: str, content: str | None = None) -> Path:
        """Resolve a file reference to a local path.

        Args:
            file_path: Local path to file, OR filename when content is provided.
            content: Base64-encoded file data. If provided, file_path is the filename.

        Returns:
            Resolved Path (saved to uploads/ if base64 content provided).
        """
        if content:
            data = base64.b64decode(content)
            return self._save_upload(file_path, data)
        return Path(file_path).expanduser().resolve()

    async def insert_file(
        self,
        file_path: str,
        content: str | None = None,
        doc_id: str | None = None,
    ) -> tuple[str, Path]:
        """Insert a file into canonical storage.

        Args:
            file_path: Local path to file, OR filename when content is provided.
            content: Base64-encoded file data. If provided, file_path is the filename.
            doc_id: Optional custom ID. Auto-generated if not provided.

        Returns:
            Tuple of (record_id, resolved_path).
        """
        path = self.resolve_file(file_path, content)
        source = f"upload:{file_path}" if content else str(path)

        # Create record and attachment
        rid = await self.insert_record(
            content=str(path),
            doc_id=doc_id,
            content_type="file_ref",
            source=source,
        )
        await self._insert_attachment(rid, path)

        return rid, path

    async def get_attachments(self, record_id: str) -> list[Attachment]:
        """Get all attachments for a record."""
        await self._ensure_tables()
        self.logger.debug(f"Getting attachments for record ID: {record_id}")

        async with self._session_factory() as session:
            stmt = select(Attachment).where(Attachment.record_id == record_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())
