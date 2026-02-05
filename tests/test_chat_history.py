"""Tests for chat history engine (with canonical wrapper)."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kbm.canonical import CanonicalStore, with_canonical
from kbm.engine import EngineProtocol
from kbm.engines.chat_history import ChatHistoryEngine


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncGenerator[EngineProtocol, None]:
    """Create a wrapped chat history engine."""
    config = MagicMock()
    config.canonical_url = f"sqlite+aiosqlite:///{tmp_path / 'canonical.db'}"

    store = CanonicalStore(config.canonical_url)
    raw_engine = ChatHistoryEngine(config, store)
    wrapped = with_canonical(store, raw_engine)
    yield wrapped

    # Cleanup - close the store
    await wrapped._store.close()  # type: ignore[union-attr]


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, engine: EngineProtocol) -> None:
        """Insert text content returns confirmation with ID."""
        result = await engine.insert("test content")
        assert result.id
        assert result.message == "Inserted"

    async def test_insert_with_custom_id(self, engine: EngineProtocol) -> None:
        """Insert with custom doc_id uses that ID."""
        result = await engine.insert("test content", doc_id="custom-id")
        assert result.id == "custom-id"

    async def test_insert_file(self, engine: EngineProtocol, tmp_path: Path) -> None:
        """Insert file stores reference in canonical."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")
        result = await engine.insert_file(str(test_file))
        assert result.id
        assert result.message == "Stored"

    async def test_insert_file_not_found(self, engine: EngineProtocol) -> None:
        """Insert file for missing file still stores reference."""
        result = await engine.insert_file("/nonexistent/file.txt")
        assert result.id
        assert result.message == "Stored"


class TestQuery:
    """Query operation tests."""

    async def test_query_matches(self, engine: EngineProtocol) -> None:
        """Query finds matching records."""
        await engine.insert("hello world")
        await engine.insert("goodbye world")

        result = await engine.query("hello")
        assert any("hello world" in r.content for r in result.results)

    async def test_query_case_insensitive(self, engine: EngineProtocol) -> None:
        """Query finds via substring match."""
        await engine.insert("Hello World")
        result = await engine.query("Hello")
        assert any("Hello World" in r.content for r in result.results)

    async def test_query_no_matches(self, engine: EngineProtocol) -> None:
        """Query returns empty results when no matches."""
        await engine.insert("hello world")
        result = await engine.query("nonexistent")
        assert result.total == 0
        assert len(result.results) == 0


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(self, engine: EngineProtocol) -> None:
        """Delete removes existing record."""
        await engine.insert("test", doc_id="to-delete")
        delete_result = await engine.delete("to-delete")
        assert delete_result.found is True

        # Should not find it anymore
        result = await engine.query("test")
        assert result.total == 0

    async def test_delete_nonexistent(self, engine: EngineProtocol) -> None:
        """Delete returns found=False for missing record."""
        result = await engine.delete("nonexistent")
        assert result.found is False


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, engine: EngineProtocol) -> None:
        """List returns record information."""
        await engine.insert("content one")
        await engine.insert("content two")

        result = await engine.list_records()
        assert len(result.records) == 2
        assert result.total == 2

    async def test_list_empty(self, engine: EngineProtocol) -> None:
        """List returns empty when no records."""
        result = await engine.list_records()
        assert len(result.records) == 0
        assert result.total == 0


class TestInfo:
    """Info operation tests."""

    async def test_info_returns_metadata(self, engine: EngineProtocol) -> None:
        """Info returns structured engine metadata."""
        await engine.insert("test")

        info = await engine.info()
        assert info.engine == "chat-history"
        assert info.records == 1
