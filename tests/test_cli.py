"""CLI command tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from kbm.cli import app

runner = CliRunner()


class TestInit:
    """Test 'kbm init' command."""

    def test_creates_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .kbm.yaml in current directory with --local."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--local"])

        assert result.exit_code == 0
        assert (tmp_path / f".kbm.{tmp_path.name}.yaml").exists()

        content = (tmp_path / f".kbm.{tmp_path.name}.yaml").read_text()
        assert f"name: {tmp_path.name}" in content

    def test_creates_global_config(self, tmp_home: Path) -> None:
        """Creates config in $KBM_HOME/memories/ for named memory."""
        result = runner.invoke(app, ["init", "test-memory"])

        assert result.exit_code == 0
        config_path = tmp_home / "memories" / "test-memory.yaml"
        assert config_path.exists()
        # Global configs now include name (single source of truth)
        assert "name: test-memory" in config_path.read_text()

    def test_creates_data_directory(self, tmp_home: Path) -> None:
        """Creates data directory in $KBM_HOME/data/."""
        runner.invoke(app, ["init", "test-memory"])

        data_path = tmp_home / "data" / "test-memory"
        assert data_path.is_dir()

    def test_fails_if_exists(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fails if config already exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / f".kbm.{tmp_path.name}.yaml").write_text("name: existing\n")

        result = runner.invoke(app, ["init", "--local"])
        assert result.exit_code != 0

    def test_force_overwrites(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--force overwrites existing config."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / f".kbm.{tmp_path.name}.yaml").write_text("name: old\n")

        result = runner.invoke(app, ["init", "--local", "--force"])
        assert result.exit_code == 0
        assert "name: old" not in (tmp_path / f".kbm.{tmp_path.name}.yaml").read_text()

    def test_engine_option(self, tmp_home: Path) -> None:
        """--engine sets the engine type."""
        result = runner.invoke(app, ["init", "rag-mem", "-e", "rag-anything"])

        assert result.exit_code == 0
        content = (tmp_home / "memories" / "rag-mem.yaml").read_text()
        assert "engine: rag-anything" in content


class TestDelete:
    """Test 'kbm delete' command."""

    def test_deletes_global_memory(self, tmp_home: Path) -> None:
        """Deletes config and data for global memory."""
        runner.invoke(app, ["init", "to-delete"])
        config_path = tmp_home / "memories" / "to-delete.yaml"
        data_path = tmp_home / "data" / "to-delete"
        assert config_path.exists()

        result = runner.invoke(app, ["delete", "to-delete", "--yes"])
        assert result.exit_code == 0
        assert not config_path.exists()
        assert not data_path.exists()

    def test_keep_data_option(self, tmp_home: Path) -> None:
        """--keep-data preserves data directory."""
        runner.invoke(app, ["init", "keep-data-test"])
        data_path = tmp_home / "data" / "keep-data-test"

        result = runner.invoke(
            app, ["delete", "keep-data-test", "--yes", "--keep-data"]
        )
        assert result.exit_code == 0
        assert data_path.is_dir()

    def test_fails_if_not_exists(self, tmp_home: Path) -> None:
        """Fails if memory doesn't exist."""
        result = runner.invoke(app, ["delete", "nonexistent", "--yes"])
        assert result.exit_code != 0


class TestList:
    """Test 'kbm list' command."""

    def test_shows_no_memories(self, tmp_home: Path) -> None:
        """Shows helpful message when no memories exist."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No memories found" in result.stdout

    def test_shows_global_memories(self, tmp_home: Path) -> None:
        """Lists global memories."""
        runner.invoke(app, ["init", "mem-one"])
        runner.invoke(app, ["init", "mem-two"])

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "mem-one" in result.stdout
        assert "mem-two" in result.stdout

    def test_shows_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shows local .kbm* files if present."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".kbm.yaml").write_text("name: local-test\nengine: chat-history\n")

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "local-test" in result.stdout
        assert "local" in result.stdout.lower()


class TestStart:
    """Test 'kbm start' command."""

    def test_starts_server_with_name(
        self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Starts server for named memory."""
        runner.invoke(app, ["init", "start-test"])

        # Mock run_server to avoid blocking
        started_config = None

        def mock_run_server(config):
            nonlocal started_config
            started_config = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)

        result = runner.invoke(app, ["start", "start-test"])
        assert result.exit_code == 0
        assert started_config is not None
        assert started_config.name == "start-test"

    def test_starts_server_with_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Starts server for local config when no name given."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--local"])

        started_config = None

        def mock_run_server(config):
            nonlocal started_config
            started_config = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)

        result = runner.invoke(app, ["start"])
        assert result.exit_code == 0
        assert started_config is not None
        assert started_config.name == tmp_path.name

    def test_starts_with_config_flag(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--config uses explicit path."""
        config = tmp_path / "custom.yaml"
        config.write_text("name: custom-server\nengine: chat-history\n")

        started_config = None

        def mock_run_server(config):
            nonlocal started_config
            started_config = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)

        result = runner.invoke(app, ["start", "--config", str(config)])
        assert result.exit_code == 0
        assert started_config is not None
        assert started_config.name == "custom-server"

    def test_transport_override(
        self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--transport overrides config."""
        runner.invoke(app, ["init", "transport-test"])

        started_config = None

        def mock_run_server(config):
            nonlocal started_config
            started_config = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)

        result = runner.invoke(app, ["start", "transport-test", "-t", "http"])
        assert result.exit_code == 0
        assert started_config is not None
        assert started_config.transport.value == "http"

    def test_host_port_override(
        self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--host and --port override config."""
        runner.invoke(app, ["init", "hostport-test"])

        started_config = None

        def mock_run_server(config):
            nonlocal started_config
            started_config = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)

        result = runner.invoke(
            app, ["start", "hostport-test", "-H", "192.168.1.1", "-p", "9000"]
        )
        assert result.exit_code == 0
        assert started_config is not None
        assert started_config.host == "192.168.1.1"
        assert started_config.port == 9000

    def test_fails_with_both_name_and_config(
        self, tmp_path: Path, tmp_home: Path
    ) -> None:
        """Fails if both name and --config are given."""
        config = tmp_path / "test.yaml"
        config.write_text("name: test\nengine: chat-history\n")

        result = runner.invoke(app, ["start", "some-name", "--config", str(config)])
        assert result.exit_code != 0

    def test_fails_without_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fails when no config found."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["start"])
        assert result.exit_code != 0


class TestStatus:
    """Test 'kbm status' command."""

    def test_shows_config(self, tmp_home: Path) -> None:
        """Shows memory configuration."""
        runner.invoke(app, ["init", "status-test"])

        result = runner.invoke(app, ["status", "status-test"])
        assert result.exit_code == 0
        assert "status-test" in result.stdout

    def test_local_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shows local config when no name given."""
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init", "--local"])

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert tmp_path.name in result.stdout

    def test_fails_without_config(
        self, tmp_path: Path, tmp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fails gracefully when no config found."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["status"])
        assert result.exit_code != 0

    def test_config_flag(self, tmp_path: Path, tmp_home: Path) -> None:
        """--config uses explicit path."""
        config = tmp_path / "custom.yaml"
        config.write_text("name: custom\nengine: chat-history\n")

        result = runner.invoke(app, ["status", "--config", str(config)])
        assert result.exit_code == 0
        assert "custom" in result.stdout
