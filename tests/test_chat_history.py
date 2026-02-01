"""Tests for chat history engine."""

from pathlib import Path

import pytest

from app.config import ChatHistoryConfig, Settings, init_settings
from app.config import reset_settings as set_settings
from engines.chat_history import ChatHistoryEngine


@pytest.fixture
def engine(
    tmp_data_dir: Path, reset_settings: None, clean_env: None
) -> ChatHistoryEngine:
    """Create a chat history engine with temp directory."""
    set_settings(None)
    init_settings()
    # Override data dir for testing
    settings = Settings(
        data_dir=tmp_data_dir,
        chat_history=ChatHistoryConfig(data_dir="records"),
    )
    set_settings(settings)
    return ChatHistoryEngine()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, engine: ChatHistoryEngine) -> None:
        """Insert text content returns confirmation message."""
        result = await engine.insert("test content")
        assert "Inserted record:" in result
        # Extract ID and verify file was created
        doc_id = result.split(": ")[1]
        record_path = engine.data_dir / f"{doc_id}.json"
        assert record_path.exists()

    async def test_insert_file(self, engine: ChatHistoryEngine, tmp_path: Path) -> None:
        """Insert file reads content from file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")

        result = await engine.insert_file(str(test_file))
        assert "test" in result  # Uses filename stem

        # Verify file was stored
        record_path = engine.data_dir / "test.json"
        assert record_path.exists()

    async def test_insert_file_not_found(self, engine: ChatHistoryEngine) -> None:
        """Insert file raises for missing file."""
        with pytest.raises(FileNotFoundError):
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
        doc_id = result.split(": ")[1]
        assert (engine.data_dir / f"{doc_id}.json").exists()

        await engine.delete(doc_id)
        assert not (engine.data_dir / f"{doc_id}.json").exists()

    async def test_delete_nonexistent(self, engine: ChatHistoryEngine) -> None:
        """Delete raises for missing record."""
        with pytest.raises(ValueError, match="not found"):
            await engine.delete("nonexistent")


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
        assert "Record count: 1" in info
