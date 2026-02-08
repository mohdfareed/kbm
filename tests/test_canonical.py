"""Tests for canonical data store."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

from kbm.store import CanonicalStore
from kbm.store.models import ContentType


@pytest.fixture
async def store(tmp_path: Path) -> AsyncGenerator[CanonicalStore, None]:
    """Create a canonical store with temp database."""
    data_path = tmp_path / "data"
    attachments_path = data_path / "attachments"
    db_path = data_path / "store.db"
    data_path.mkdir(parents=True, exist_ok=True)
    s = CanonicalStore(
        f"sqlite+aiosqlite:///{db_path}", attachments_path=attachments_path
    )
    yield s
    await s.close()


class TestCanonicalStore:
    """Core store operations."""

    async def test_initialize_creates_db(self, tmp_path: Path) -> None:
        """Initialize creates the database file."""
        db_path = tmp_path / "canonical.db"
        store = CanonicalStore(
            f"sqlite+aiosqlite:///{db_path}",
            attachments_path=tmp_path / "attachments",
        )
        await store.initialize()
        assert db_path.exists()
        await store.close()

    async def test_insert_record(self, store: CanonicalStore) -> None:
        """Insert returns record ID."""
        rid = await store.insert_record("test content")
        assert rid
        assert len(rid) == 36  # UUID format

    async def test_insert_with_custom_id(self, store: CanonicalStore) -> None:
        """Insert with custom ID uses that ID."""
        rid = await store.insert_record("test content", doc_id="custom-id")
        assert rid == "custom-id"

    async def test_get_record(self, store: CanonicalStore) -> None:
        """Get retrieves inserted record."""
        rid = await store.insert_record("test content", doc_id="test-id")
        record = await store.get_record(rid)
        assert record is not None
        assert record.id == "test-id"
        assert record.content == "test content"
        assert record.content_type == ContentType.TEXT

    async def test_get_nonexistent(self, store: CanonicalStore) -> None:
        """Get returns None for nonexistent record."""
        record = await store.get_record("nonexistent")
        assert record is None

    async def test_delete_record(self, store: CanonicalStore) -> None:
        """Delete removes record."""
        rid = await store.insert_record("test content", doc_id="to-delete")
        assert await store.delete_record(rid)
        assert await store.get_record(rid) is None

    async def test_delete_nonexistent(self, store: CanonicalStore) -> None:
        """Delete returns False for nonexistent record."""
        assert not await store.delete_record("nonexistent")

    async def test_list_records(self, store: CanonicalStore) -> None:
        """List returns all records."""
        await store.insert_record("first", doc_id="r1")
        await store.insert_record("second", doc_id="r2")

        records = await store.list_records()
        assert len(records) == 2
        ids = {r.id for r in records}
        assert ids == {"r1", "r2"}

    async def test_list_with_pagination(self, store: CanonicalStore) -> None:
        """List respects limit and offset."""
        for i in range(5):
            await store.insert_record(f"content-{i}", doc_id=f"r{i}")

        records = await store.list_records(limit=2, offset=1)
        assert len(records) == 2

    async def test_count_records(self, store: CanonicalStore) -> None:
        """Count returns total record count."""
        assert await store.count_records() == 0
        await store.insert_record("first")
        await store.insert_record("second")
        assert await store.count_records() == 2

    async def test_search_records(self, store: CanonicalStore) -> None:
        """Search finds matching records."""
        await store.insert_record("hello world", doc_id="r1")
        await store.insert_record("goodbye world", doc_id="r2")

        results = await store.search_records("hello")
        assert len(results) == 1
        assert results[0].content == "hello world"


class TestFileInserts:
    """File insert operations - always copy to attachments/."""

    async def test_insert_local_file(
        self, store: CanonicalStore, tmp_path: Path
    ) -> None:
        """Local file insert copies file to attachments/ and stores relative path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        rid, path = await store.insert_file(str(test_file))

        assert rid
        # File should be in attachments/
        assert "attachments" in str(path)
        assert path.exists()
        assert path.read_text() == "hello world"

        # Record content should be a relative path
        record = await store.get_record(rid)
        assert record is not None
        assert record.content_type == ContentType.FILE
        assert not record.content.startswith("attachments/")
        assert record.source == str(test_file)

    async def test_insert_base64_file(self, store: CanonicalStore) -> None:
        """Base64 file insert saves to attachments/ and stores relative path."""
        import base64

        content = base64.b64encode(b"hello world").decode()
        rid, path = await store.insert_file("test.txt", content=content)

        assert rid
        assert path.name.endswith(".txt")
        assert path.read_bytes() == b"hello world"

        record = await store.get_record(rid)
        assert record is not None
        assert record.content_type == ContentType.FILE
        assert not record.content.startswith("attachments/")
        assert record.source == "test.txt"

    async def test_file_deduplication(
        self, store: CanonicalStore, tmp_path: Path
    ) -> None:
        """Inserting the same file twice deduplicates in attachments/."""
        test_file = tmp_path / "doc.txt"
        test_file.write_text("same content")

        _, path1 = await store.insert_file(str(test_file))
        _, path2 = await store.insert_file(str(test_file))

        assert path1 == path2  # same deduped path

    async def test_file_not_found(self, store: CanonicalStore) -> None:
        """Insert file with nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await store.insert_file("/nonexistent/file.txt")

    async def test_relative_path_rejected(self, store: CanonicalStore) -> None:
        """Insert file with relative path raises ValueError."""
        with pytest.raises(ValueError, match="absolute"):
            await store.insert_file("relative/path.txt")
