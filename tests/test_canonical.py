"""Tests for canonical data store."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from kbm.canonical import Attachment, CanonicalStore, Record, with_canonical
from kbm.canonical.wrapper import CanonicalEngineWrapper
from kbm.engine import Operation


@pytest.fixture
async def store(tmp_path: Path) -> AsyncGenerator[CanonicalStore, None]:
    """Create a canonical store with temp database."""
    db_path = tmp_path / "canonical.db"
    s = CanonicalStore(f"sqlite+aiosqlite:///{db_path}")
    yield s
    await s.close()


@pytest.fixture
def mock_config(tmp_path: Path) -> MagicMock:
    """Create a mock config with canonical_url."""
    config = MagicMock()
    config.canonical_url = f"sqlite+aiosqlite:///{tmp_path / 'canonical.db'}"
    return config


class TestCanonicalStore:
    """Core store operations."""

    async def test_initialize_creates_db(self, tmp_path: Path) -> None:
        """Initialize creates the database file."""
        db_path = tmp_path / "canonical.db"
        store = CanonicalStore(f"sqlite+aiosqlite:///{db_path}")
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
        assert record.content_type == "text"

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


class TestAttachments:
    """Attachment operations."""

    async def test_insert_attachment(self, store: CanonicalStore) -> None:
        """Insert attachment returns ID."""
        rid = await store.insert_record("test", doc_id="r1")
        aid = await store.insert_attachment(
            record_id=rid,
            file_name="test.txt",
            file_path="/path/to/test.txt",
            mime_type="text/plain",
            size_bytes=100,
        )
        assert aid
        assert len(aid) == 36

    async def test_get_attachments(self, store: CanonicalStore) -> None:
        """Get attachments returns all for record."""
        rid = await store.insert_record("test", doc_id="r1")
        await store.insert_attachment(
            record_id=rid, file_name="a.txt", file_path="/a.txt"
        )
        await store.insert_attachment(
            record_id=rid, file_name="b.txt", file_path="/b.txt"
        )

        attachments = await store.get_attachments(rid)
        assert len(attachments) == 2
        names = {a.file_name for a in attachments}
        assert names == {"a.txt", "b.txt"}


class TestCanonicalWrapper:
    """Engine wrapper tests."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        """Create a mock engine with async methods."""
        from kbm.models import DeleteResponse, InsertResponse, QueryResponse

        engine = MagicMock()
        engine.supported_operations = frozenset(
            {Operation.INSERT, Operation.QUERY, Operation.DELETE}
        )

        # Make methods async-compatible with proper return types
        def insert_side_effect(
            content: str, doc_id: str | None = None
        ) -> InsertResponse:
            return InsertResponse(id=doc_id or "generated-id", message="Inserted")

        def delete_side_effect(record_id: str) -> DeleteResponse:
            return DeleteResponse(id=record_id, found=True, message="Deleted")

        engine.insert = AsyncMock(side_effect=insert_side_effect)
        engine.query = AsyncMock(
            return_value=QueryResponse(results=[], query="", total=0)
        )
        engine.delete = AsyncMock(side_effect=delete_side_effect)
        return engine

    @pytest.fixture
    def wrapped(
        self, store: CanonicalStore, mock_engine: MagicMock
    ) -> CanonicalEngineWrapper:
        """Create a wrapped engine."""
        return CanonicalEngineWrapper(mock_engine, store)

    async def test_insert_persists_to_canonical(
        self, wrapped: CanonicalEngineWrapper, store: CanonicalStore
    ) -> None:
        """Insert writes to canonical store."""
        result = await wrapped.insert("test content")
        assert result.id
        assert result.message == "Inserted"
        record = await store.get_record(result.id)
        assert record is not None
        assert record.content == "test content"

    async def test_insert_calls_engine(
        self, wrapped: CanonicalEngineWrapper, mock_engine: MagicMock
    ) -> None:
        """Insert also calls underlying engine."""
        await wrapped.insert("test content")
        mock_engine.insert.assert_called_once()

    async def test_query_delegates_to_engine(
        self, wrapped: CanonicalEngineWrapper, mock_engine: MagicMock
    ) -> None:
        """Query goes to engine (optimized indexes)."""
        from kbm.models import QueryResponse

        mock_engine.query = AsyncMock(
            return_value=QueryResponse(results=[], query="search term", total=0)
        )
        result = await wrapped.query("search term")
        mock_engine.query.assert_called_once_with("search term", 10)
        assert result.query == "search term"

    async def test_delete_removes_from_canonical(
        self, wrapped: CanonicalEngineWrapper, store: CanonicalStore
    ) -> None:
        """Delete removes from canonical store."""
        await wrapped.insert("test content", doc_id="to-delete")
        result = await wrapped.delete("to-delete")
        assert result.found is True
        assert await store.get_record("to-delete") is None

    async def test_list_records_from_canonical(
        self, wrapped: CanonicalEngineWrapper, store: CanonicalStore
    ) -> None:
        """List reads from canonical store."""
        await wrapped.insert("first", doc_id="r1")
        await wrapped.insert("second", doc_id="r2")

        result = await wrapped.list_records()
        ids = {r.id for r in result.records}
        assert "r1" in ids
        assert "r2" in ids


class TestWithCanonical:
    """Factory function tests."""

    def test_wraps_engine(self, mock_config: MagicMock) -> None:
        """Always wraps engines to add canonical storage."""
        engine = MagicMock()
        engine.supported_operations = frozenset({Operation.QUERY})

        wrapped = with_canonical(mock_config, engine)
        assert isinstance(wrapped, CanonicalEngineWrapper)

    def test_adds_write_operations(self, mock_config: MagicMock) -> None:
        """Wrapper adds write operations engine doesn't have."""
        engine = MagicMock()
        engine.supported_operations = frozenset({Operation.QUERY, Operation.INFO})

        wrapped = with_canonical(mock_config, engine)
        assert Operation.INSERT in wrapped.supported_operations
        assert Operation.DELETE in wrapped.supported_operations
        assert Operation.LIST_RECORDS in wrapped.supported_operations
