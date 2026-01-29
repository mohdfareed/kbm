"""Tests for helper utilities."""

from pathlib import Path

import pytest

from app.helpers import find_file


class TestFindFile:
    """Tests for find_file utility."""

    def test_find_in_current_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finds file in current directory."""
        target = tmp_path / "target.txt"
        target.touch()
        monkeypatch.chdir(tmp_path)

        result = find_file(["target.txt"])
        assert result == target

    def test_find_in_parent_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finds file in parent directory."""
        target = tmp_path / "target.txt"
        target.touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        result = find_file(["target.txt"])
        assert result == target

    def test_find_priority_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns first match from names list."""
        first = tmp_path / "first.txt"
        second = tmp_path / "second.txt"
        first.touch()
        second.touch()
        monkeypatch.chdir(tmp_path)

        result = find_file(["first.txt", "second.txt"])
        assert result == first

    def test_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns None when file not found."""
        monkeypatch.chdir(tmp_path)
        result = find_file(["nonexistent.txt"])
        assert result is None

    def test_skips_directories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ignores directories with matching names."""
        (tmp_path / "target.txt").mkdir()  # Directory, not file
        monkeypatch.chdir(tmp_path)

        result = find_file(["target.txt"])
        assert result is None
