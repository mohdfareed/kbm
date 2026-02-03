"""CLI command tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from kbm.cli.app import cli_app

runner = CliRunner()


class TestInit:
    """Test 'kbm init' command."""

    def test_creates_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .kbm.yaml in current directory."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli_app, ["init"])

        assert result.exit_code == 0
        assert (tmp_path / ".kbm.yaml").exists()

        content = (tmp_path / ".kbm.yaml").read_text()
        assert f"name: {tmp_path.name}" in content

    def test_creates_global_config(self, tmp_home: Path) -> None:
        """Creates config in $KBM_HOME/memories/ for named memory."""
        result = runner.invoke(cli_app, ["init", "test-memory"])

        assert result.exit_code == 0
        config_path = tmp_home / "memories" / "test-memory.yaml"
        assert config_path.exists()
        assert "name: test-memory" in config_path.read_text()

    def test_creates_data_directory(self, tmp_home: Path) -> None:
        """Creates data directory in $KBM_HOME/data/."""
        runner.invoke(cli_app, ["init", "test-memory"])

        data_path = tmp_home / "data" / "test-memory"
        assert data_path.is_dir()

    def test_fails_if_exists(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fails if config already exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".kbm.yaml").write_text("name: existing\n")

        result = runner.invoke(cli_app, ["init"])
        assert result.exit_code != 0

    def test_force_overwrites(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--force overwrites existing config."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".kbm.yaml").write_text("name: old\n")

        result = runner.invoke(cli_app, ["init", "--force"])
        assert result.exit_code == 0
        assert "name: old" not in (tmp_path / ".kbm.yaml").read_text()

    def test_engine_option(self, tmp_home: Path) -> None:
        """--engine sets the engine type."""
        result = runner.invoke(cli_app, ["init", "rag-mem", "-e", "rag-anything"])

        assert result.exit_code == 0
        content = (tmp_home / "memories" / "rag-mem.yaml").read_text()
        assert "engine: rag-anything" in content


class TestDelete:
    """Test 'kbm delete' command."""

    def test_deletes_global_memory(self, tmp_home: Path) -> None:
        """Deletes config and data for global memory."""
        runner.invoke(cli_app, ["init", "to-delete"])
        config_path = tmp_home / "memories" / "to-delete.yaml"
        data_path = tmp_home / "data" / "to-delete"
        assert config_path.exists()

        result = runner.invoke(cli_app, ["delete", "to-delete", "--yes"])
        assert result.exit_code == 0
        assert not config_path.exists()
        assert not data_path.exists()

    def test_keep_data_option(self, tmp_home: Path) -> None:
        """--keep-data preserves data directory."""
        runner.invoke(cli_app, ["init", "keep-data-test"])
        data_path = tmp_home / "data" / "keep-data-test"

        result = runner.invoke(
            cli_app, ["delete", "keep-data-test", "--yes", "--keep-data"]
        )
        assert result.exit_code == 0
        assert data_path.is_dir()

    def test_fails_if_not_exists(self, tmp_home: Path) -> None:
        """Fails if memory doesn't exist."""
        result = runner.invoke(cli_app, ["delete", "nonexistent", "--yes"])
        assert result.exit_code != 0


class TestList:
    """Test 'kbm list' command."""

    def test_shows_no_memories(self, tmp_home: Path) -> None:
        """Shows helpful message when no memories exist."""
        result = runner.invoke(cli_app, ["list"])
        assert result.exit_code == 0
        assert "No memories found" in result.stdout

    def test_shows_global_memories(self, tmp_home: Path) -> None:
        """Lists global memories."""
        runner.invoke(cli_app, ["init", "mem-one"])
        runner.invoke(cli_app, ["init", "mem-two"])

        result = runner.invoke(cli_app, ["list"])
        assert result.exit_code == 0
        assert "mem-one" in result.stdout
        assert "mem-two" in result.stdout

    def test_shows_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shows local .kbm.yaml if present."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".kbm.yaml").write_text("name: local-test\nengine: chat-history\n")

        result = runner.invoke(cli_app, ["list"])
        assert result.exit_code == 0
        assert "Local" in result.stdout


class TestStatus:
    """Test 'kbm status' command."""

    def test_shows_config(self, tmp_home: Path) -> None:
        """Shows memory configuration."""
        runner.invoke(cli_app, ["init", "status-test"])

        result = runner.invoke(cli_app, ["status", "status-test"])
        assert result.exit_code == 0
        assert "status-test" in result.stdout

    def test_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shows local config when no name given."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".kbm.yaml").write_text("name: local\nengine: chat-history\n")

        result = runner.invoke(cli_app, ["status"])
        assert result.exit_code == 0
        assert "local" in result.stdout

    def test_fails_without_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fails gracefully when no config found."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli_app, ["status"])
        assert result.exit_code != 0

    def test_config_flag(self, tmp_path: Path, tmp_home: Path) -> None:
        """--config uses explicit path."""
        config = tmp_path / "custom.yaml"
        config.write_text("name: custom\nengine: chat-history\n")

        result = runner.invoke(cli_app, ["status", "--config", str(config)])
        assert result.exit_code == 0
        assert "custom" in result.stdout
