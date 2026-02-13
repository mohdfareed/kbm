"""Tests for chat history engine via MemoryTools."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from kbm.engines.chat_history import ChatHistoryEngine
from kbm.mcp.tools import MemoryTools
from kbm.store import CanonStore


@pytest.fixture
async def tools(tmp_path: Path) -> AsyncGenerator[MemoryTools, None]:
    """Create MemoryTools backed by a ChatHistoryEngine."""
    config = MagicMock()
    config.engine = "chat-history"
    data_path = tmp_path / "data"
    attachments_path = data_path / "attachments"
    data_path.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{data_path / 'store.db'}"

    store = CanonStore(db_url, attachments_path=attachments_path)
    engine = ChatHistoryEngine(config, store)
    yield MemoryTools(engine, store)
    await store.close()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, tools: MemoryTools) -> None:
        """Insert text content returns confirmation with ID."""
        result = await tools.insert("test content")
        assert result.id
        assert result.message == "Inserted"

    async def test_insert_file(self, tools: MemoryTools, tmp_path: Path) -> None:
        """Insert file stores reference in canonical."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")
        result = await tools.insert_file(str(test_file))
        assert result.id

    async def test_insert_file_not_found(self, tools: MemoryTools) -> None:
        """Insert file for missing file raises FileNotFoundError."""
        with pytest.raises(ToolError):
            await tools.insert_file("/nonexistent/file.txt")


class TestQuery:
    """Query operation tests."""

    async def test_query_matches(self, tools: MemoryTools) -> None:
        """Query finds matching records."""
        await tools.insert("hello world")
        await tools.insert("goodbye world")

        result = await tools.query("hello")
        assert any("hello world" in r.content for r in result.results)

    async def test_query_case_insensitive(self, tools: MemoryTools) -> None:
        """Query finds via substring match."""
        await tools.insert("Hello World")
        result = await tools.query("Hello")
        assert any("Hello World" in r.content for r in result.results)

    async def test_query_no_matches(self, tools: MemoryTools) -> None:
        """Query returns empty results when no matches."""
        await tools.insert("hello world")
        result = await tools.query("nonexistent")
        assert result.total == 0
        assert len(result.results) == 0


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(self, tools: MemoryTools) -> None:
        """Delete removes existing record."""
        insert_result = await tools.insert("test")
        delete_result = await tools.delete(insert_result.id)
        assert delete_result.found is True

        # Should not find it anymore
        result = await tools.query("test")
        assert result.total == 0

    async def test_delete_nonexistent(self, tools: MemoryTools) -> None:
        """Delete returns found=False for missing record."""
        result = await tools.delete("nonexistent")
        assert result.found is False


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, tools: MemoryTools) -> None:
        """List returns record information."""
        await tools.insert("content one")
        await tools.insert("content two")

        result = await tools.list_records()
        assert len(result.records) == 2
        assert result.total == 2

    async def test_list_empty(self, tools: MemoryTools) -> None:
        """List returns empty when no records."""
        result = await tools.list_records()
        assert len(result.records) == 0
        assert result.total == 0


class TestInfo:
    """Info operation tests."""

    async def test_info_returns_metadata(self, tools: MemoryTools) -> None:
        """Info returns structured engine metadata."""
        await tools.insert("test")

        info = await tools.info()
        assert info.engine == "chat-history"


class TestErrorConversion:
    """Exception → ToolError conversion in MemoryTools."""

    async def test_exception_becomes_tool_error(self, tools: MemoryTools) -> None:
        """Exception raised in engine is converted to ToolError."""
        with patch.object(
            tools.engine,  # type: ignore[arg-type]
            "query",
            new_callable=AsyncMock,
            side_effect=ValueError("bad query"),
        ):
            with pytest.raises(ToolError, match="bad query"):
                await tools.query("anything")

    async def test_tool_error_passes_through(self, tools: MemoryTools) -> None:
        """ToolError raised in engine propagates unchanged."""
        with patch.object(
            tools.engine,  # type: ignore[arg-type]
            "query",
            new_callable=AsyncMock,
            side_effect=ToolError("already wrapped"),
        ):
            with pytest.raises(ToolError, match="already wrapped"):
                await tools.query("anything")
