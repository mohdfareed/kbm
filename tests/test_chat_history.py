"""Tests for chat history engine."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kbm.engines.chat_history import ChatHistoryEngine


@pytest.fixture
def engine(tmp_path: Path) -> ChatHistoryEngine:
    """Create a chat history engine with temp directory."""
    # Mock a Config object with just the needed attribute
    config = MagicMock()
    config.engine_data_path = tmp_path / "chat-history"
    return ChatHistoryEngine(config)


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, engine: ChatHistoryEngine) -> None:
        """Insert text content returns confirmation message."""
        result = await engine.insert("test content")
        assert "Inserted:" in result
        # Extract ID and verify file was created
        doc_id = result.split(": ")[1]
        record_path = engine.data_dir / f"{doc_id}.json"
        assert record_path.exists()

    async def test_insert_with_custom_id(self, engine: ChatHistoryEngine) -> None:
        """Insert with custom doc_id uses that ID."""
        result = await engine.insert("test content", doc_id="custom-id")
        assert "custom-id" in result
        assert (engine.data_dir / "custom-id.json").exists()

    async def test_insert_file(self, engine: ChatHistoryEngine, tmp_path: Path) -> None:
        """Insert file raises NotImplementedError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")

        with pytest.raises(NotImplementedError):
            await engine.insert_file(str(test_file))

    async def test_insert_file_not_found(self, engine: ChatHistoryEngine) -> None:
        """Insert file raises NotImplementedError (not FileNotFoundError)."""
        with pytest.raises(NotImplementedError):
            await engine.insert_file("/nonexistent/file.txt")


class TestQuery:
    """Query operation tests."""

    async def test_query_matches(self, engine: ChatHistoryEngine) -> None:
        """Query finds matching records."""
        await engine.insert("hello world")
        await engine.insert("goodbye world")

        result = await engine.query("hello")
        assert "hello world" in result

    async def test_query_case_insensitive(self, engine: ChatHistoryEngine) -> None:
        """Query is case-insensitive."""
        await engine.insert("Hello World")
        result = await engine.query("hello")
        assert "Hello World" in result

    async def test_query_no_matches(self, engine: ChatHistoryEngine) -> None:
        """Query returns message when no matches."""
        await engine.insert("hello world")
        result = await engine.query("nonexistent")
        assert "No matching records" in result


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(self, engine: ChatHistoryEngine) -> None:
        """Delete removes existing record."""
        result = await engine.insert("test")
        doc_id = result.split(": ")[1]  # "Inserted: <id>"
        assert (engine.data_dir / f"{doc_id}.json").exists()

        await engine.delete(doc_id)
        assert not (engine.data_dir / f"{doc_id}.json").exists()

    async def test_delete_nonexistent(self, engine: ChatHistoryEngine) -> None:
        """Delete returns message for missing record."""
        result = await engine.delete("nonexistent")
        assert "not found" in result.lower()


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, engine: ChatHistoryEngine) -> None:
        """List returns record information."""
        await engine.insert("content one")
        await engine.insert("content two")

        result = await engine.list_records()
        # Result is a string with record IDs
        assert result.count("[") == 2  # Two records listed

    async def test_list_empty(self, engine: ChatHistoryEngine) -> None:
        """List returns message when empty."""
        result = await engine.list_records()
        assert "No records found" in result


class TestInfo:
    """Info operation tests."""

    async def test_info_returns_metadata(self, engine: ChatHistoryEngine) -> None:
        """Info returns engine metadata as string."""
        await engine.insert("test")

        info = await engine.info()
        assert "chat-history" in info
        assert "Records: 1" in info
