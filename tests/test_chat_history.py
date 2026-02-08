"""Tests for chat history engine."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from kbm.engines.base_engine import EngineBase
from kbm.engines.chat_history import ChatHistoryEngine
from kbm.store import CanonicalStore


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncGenerator[EngineBase, None]:
    """Create a chat history engine with canonical store."""
    config = MagicMock()
    data_path = tmp_path / "data"
    attachments_path = data_path / "attachments"
    data_path.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{data_path / 'store.db'}"

    store = CanonicalStore(db_url, attachments_path=attachments_path)
    eng = ChatHistoryEngine(config, store)
    yield eng
    await store.close()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, engine: EngineBase) -> None:
        """Insert text content returns confirmation with ID."""
        result = await engine.insert("test content")
        assert result.id
        assert result.message == "Inserted"

    async def test_insert_with_custom_id(self, engine: EngineBase) -> None:
        """Insert with custom doc_id uses that ID."""
        result = await engine.insert("test content", doc_id="custom-id")
        assert result.id == "custom-id"

    async def test_insert_file(self, engine: EngineBase, tmp_path: Path) -> None:
        """Insert file stores reference in canonical."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")
        result = await engine.insert_file(str(test_file))
        assert result.id

    async def test_insert_file_not_found(self, engine: EngineBase) -> None:
        """Insert file for missing file raises FileNotFoundError."""
        with pytest.raises(ToolError):
            await engine.insert_file("/nonexistent/file.txt")


class TestQuery:
    """Query operation tests."""

    async def test_query_matches(self, engine: EngineBase) -> None:
        """Query finds matching records."""
        await engine.insert("hello world")
        await engine.insert("goodbye world")

        result = await engine.query("hello")
        assert any("hello world" in r.content for r in result.results)

    async def test_query_case_insensitive(self, engine: EngineBase) -> None:
        """Query finds via substring match."""
        await engine.insert("Hello World")
        result = await engine.query("Hello")
        assert any("Hello World" in r.content for r in result.results)

    async def test_query_no_matches(self, engine: EngineBase) -> None:
        """Query returns empty results when no matches."""
        await engine.insert("hello world")
        result = await engine.query("nonexistent")
        assert result.total == 0
        assert len(result.results) == 0


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(self, engine: EngineBase) -> None:
        """Delete removes existing record."""
        await engine.insert("test", doc_id="to-delete")
        delete_result = await engine.delete("to-delete")
        assert delete_result.found is True

        # Should not find it anymore
        result = await engine.query("test")
        assert result.total == 0

    async def test_delete_nonexistent(self, engine: EngineBase) -> None:
        """Delete returns found=False for missing record."""
        result = await engine.delete("nonexistent")
        assert result.found is False


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, engine: EngineBase) -> None:
        """List returns record information."""
        await engine.insert("content one")
        await engine.insert("content two")

        result = await engine.list_records()
        assert len(result.records) == 2
        assert result.total == 2

    async def test_list_empty(self, engine: EngineBase) -> None:
        """List returns empty when no records."""
        result = await engine.list_records()
        assert len(result.records) == 0
        assert result.total == 0


class TestInfo:
    """Info operation tests."""

    async def test_info_returns_metadata(self, engine: EngineBase) -> None:
        """Info returns structured engine metadata."""
        await engine.insert("test")

        info = await engine.info()
        assert info.engine == "chat-history"
        assert info.records == 1


class TestErrorConversion:
    """KBMError → ToolError conversion in template methods."""

    async def test_exception_becomes_tool_error(self, engine: EngineBase) -> None:
        """Exception raised in a hook is converted to ToolError."""
        with patch.object(
            engine,
            "_query",
            new_callable=AsyncMock,
            side_effect=ValueError("bad query"),
        ):
            with pytest.raises(ToolError, match="bad query"):
                await engine.query("anything")

    async def test_tool_error_passes_through(self, engine: EngineBase) -> None:
        """ToolError raised in a hook propagates unchanged."""
        with patch.object(
            engine,
            "_query",
            new_callable=AsyncMock,
            side_effect=ToolError("already wrapped"),
        ):
            with pytest.raises(ToolError, match="already wrapped"):
                await engine.query("anything")
