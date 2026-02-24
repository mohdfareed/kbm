"""Tests for markdown engine via MemoryTools."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from fastmcp.exceptions import ToolError

from kbm.engines.markdown import MarkdownEngine
from kbm.mcp.tools import MemoryTools
from kbm.store import CanonStore


@pytest.fixture
async def md_dir(tmp_path: Path) -> Path:
    """Return the markdown output directory."""
    return tmp_path / "data" / "markdown"


@pytest.fixture
async def tools(tmp_path: Path, md_dir: Path) -> AsyncGenerator[MemoryTools, None]:
    """Create MemoryTools backed by a MarkdownEngine."""
    config = MagicMock()
    config.engine = "markdown"
    config.settings.data_path = tmp_path / "data"

    data_path = tmp_path / "data"
    attachments_path = data_path / "attachments"
    data_path.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{data_path / 'store.db'}"

    store = CanonStore(db_url, attachments_path=attachments_path)
    engine = MarkdownEngine(config, store)
    yield MemoryTools(engine, store)
    await store.close()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(self, tools: MemoryTools) -> None:
        """Insert text content returns confirmation with ID."""
        result = await tools.insert("test content")
        assert result.id
        assert result.message == "Inserted"

    async def test_insert_creates_md_file(
        self, tools: MemoryTools, md_dir: Path
    ) -> None:
        """Insert creates a .md file in the markdown directory."""
        result = await tools.insert("hello world")
        md_file = md_dir / f"{result.id}.md"
        assert md_file.exists()

    async def test_md_file_contains_content(
        self, tools: MemoryTools, md_dir: Path
    ) -> None:
        """The .md file body contains the inserted content."""
        result = await tools.insert("some important note")
        md_file = md_dir / f"{result.id}.md"
        text = md_file.read_text()
        assert "some important note" in text

    async def test_md_file_has_frontmatter(
        self, tools: MemoryTools, md_dir: Path
    ) -> None:
        """The .md file has YAML frontmatter with id and created_at."""
        result = await tools.insert("frontmatter test")
        md_file = md_dir / f"{result.id}.md"
        text = md_file.read_text()

        # Parse frontmatter
        parts = text.split("---")
        assert len(parts) >= 3, "Expected YAML frontmatter delimiters"
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["id"] == result.id
        assert "created_at" in frontmatter


class TestQuery:
    """Query operation tests."""

    async def test_query_matches(self, tools: MemoryTools) -> None:
        """Query finds matching records."""
        await tools.insert("hello world")
        await tools.insert("goodbye world")

        result = await tools.query("hello")
        assert any("hello world" in r.content for r in result.results)

    async def test_query_no_matches(self, tools: MemoryTools) -> None:
        """Query returns empty results when no matches."""
        await tools.insert("hello world")
        result = await tools.query("nonexistent")
        assert result.total == 0
        assert len(result.results) == 0


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(self, tools: MemoryTools, md_dir: Path) -> None:
        """Delete removes existing record and its .md file."""
        insert_result = await tools.insert("test")
        md_file = md_dir / f"{insert_result.id}.md"
        assert md_file.exists()

        delete_result = await tools.delete(insert_result.id)
        assert delete_result.found is True
        assert not md_file.exists()

    async def test_delete_nonexistent(self, tools: MemoryTools) -> None:
        """Delete returns found=False for missing record."""
        result = await tools.delete("nonexistent")
        assert result.found is False

    async def test_delete_removes_from_search(self, tools: MemoryTools) -> None:
        """Deleted record no longer appears in query results."""
        insert_result = await tools.insert("unique phrase")
        await tools.delete(insert_result.id)

        result = await tools.query("unique phrase")
        assert result.total == 0


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
        assert info.engine == "markdown"
        assert info.records == 1

    async def test_info_instructions(self, tools: MemoryTools) -> None:
        """Info includes engine-specific instructions."""
        info = await tools.info()
        assert "markdown" in info.instructions.lower()


class TestGetRecord:
    """Get record tests."""

    async def test_get_existing(self, tools: MemoryTools) -> None:
        """Get record returns full content."""
        insert_result = await tools.insert("detailed content here")
        record = await tools.get_record(insert_result.id)
        assert record.content == "detailed content here"
        assert record.id == insert_result.id

    async def test_get_nonexistent(self, tools: MemoryTools) -> None:
        """Get record raises ToolError for missing record."""
        with pytest.raises(ToolError):
            await tools.get_record("nonexistent")


class TestMarkdownFileFormat:
    """Tests verifying the markdown file format is human-friendly."""

    async def test_file_is_valid_markdown(
        self, tools: MemoryTools, md_dir: Path
    ) -> None:
        """The output file is valid markdown with frontmatter."""
        result = await tools.insert("# My Note\n\nThis is a paragraph.")
        md_file = md_dir / f"{result.id}.md"
        text = md_file.read_text()

        # Should start with frontmatter delimiter
        assert text.startswith("---\n")
        # Content should appear after the second delimiter
        assert "# My Note" in text
        assert "This is a paragraph." in text

    async def test_multiple_inserts_create_separate_files(
        self, tools: MemoryTools, md_dir: Path
    ) -> None:
        """Each insert creates its own .md file."""
        r1 = await tools.insert("first note")
        r2 = await tools.insert("second note")

        assert (md_dir / f"{r1.id}.md").exists()
        assert (md_dir / f"{r2.id}.md").exists()
        assert r1.id != r2.id
