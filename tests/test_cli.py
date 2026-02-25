"""CLI command tests.

Tests compose CLI commands to verify behaviors (init → memory → start)
rather than asserting internal file paths or directory layouts.
"""

from pathlib import Path

import pytest
from click.testing import Result
from typer.testing import CliRunner

from kbm.cli import app

runner = CliRunner()


# -- Helpers ------------------------------------------------------------------


def invoke(*args: str, home: Path | None = None, **kwargs) -> Result:
    """Invoke CLI, optionally rooted at a specific home."""
    cmd: list[str] = []
    if home:
        cmd.extend(["-r", str(home)])
    cmd.extend(args)
    return runner.invoke(app, cmd, **kwargs)


def init_memory(name: str, home: Path | None = None, **kwargs) -> None:
    """Initialize a memory, asserting success."""
    args = ["init", name]
    for k, v in kwargs.items():
        args.extend([f"--{k}", str(v)])
    result = invoke(*args, home=home)
    assert result.exit_code == 0, result.stdout


# -- Init ---------------------------------------------------------------------


class TestInit:
    """Test 'kbm init' command."""

    def test_init_and_memory(self, tmp_home: Path) -> None:
        """Initialized memory is queryable via memory command."""
        init_memory("my-mem")
        result = runner.invoke(app, ["memory", "my-mem"])
        assert result.exit_code == 0

    def test_default_name_is_cwd(self, tmp_home: Path) -> None:
        """No name argument uses current directory name."""
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Default name was resolved at import time from cwd
        from kbm.cli import MemoryNameArg

        default_name = MemoryNameArg.default
        result = runner.invoke(app, ["memory", default_name])
        assert result.exit_code == 0

    def test_rejects_duplicate(self, tmp_home: Path) -> None:
        """Cannot init twice without --force."""
        init_memory("dup")
        result = runner.invoke(app, ["init", "dup"])
        assert result.exit_code != 0

    def test_force_overwrites(self, tmp_home: Path) -> None:
        """--force allows re-initialization."""
        init_memory("dup")
        result = runner.invoke(app, ["init", "dup", "--force"])
        assert result.exit_code == 0

    def test_engine_option(self, tmp_home: Path) -> None:
        """--engine is reflected in memory output."""
        init_memory("rag-mem", engine="rag-anything")
        result = runner.invoke(app, ["memory", "rag-mem"])
        assert result.exit_code == 0
        assert "rag-anything" in result.stdout


# -- Home & Settings ----------------------------------------------------------


class TestHome:
    """Test 'kbm home' command."""

    def test_prints_home(self, tmp_home: Path) -> None:
        """Home prints the application home directory."""
        result = runner.invoke(app, ["home"])
        assert result.exit_code == 0
        # Rich may wrap the long path, so check the basename
        assert tmp_home.name in result.stdout


class TestSettings:
    """Test 'kbm settings' command."""

    def test_prints_settings(self, tmp_home: Path) -> None:
        """Settings prints YAML config."""
        result = runner.invoke(app, ["settings"])
        assert result.exit_code == 0
        assert "debug" in result.stdout

    def test_all_flag(self, tmp_home: Path) -> None:
        """--all includes computed fields."""
        result = runner.invoke(app, ["settings", "--all", "True"])
        assert result.exit_code == 0
        assert "config_path" in result.stdout


class TestVersion:
    """Test version flag."""

    def test_version(self, tmp_home: Path) -> None:
        """--version prints version and exits."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "kbm" in result.stdout.lower()


# -- Memory -------------------------------------------------------------------


class TestMemory:
    """Test 'kbm memory' command."""

    def test_shows_config(self, tmp_home: Path) -> None:
        """Memory command displays config."""
        init_memory("my-mem")
        result = runner.invoke(app, ["memory", "my-mem"])
        assert result.exit_code == 0
        assert "chat-history" in result.stdout

    def test_nonexistent_fails(self, tmp_home: Path) -> None:
        """Memory for nonexistent memory fails."""
        result = runner.invoke(app, ["memory", "ghost"])
        assert result.exit_code != 0


# -- Start --------------------------------------------------------------------


class TestStart:
    """Test 'kbm start' command."""

    @pytest.fixture
    def capture_server(self, monkeypatch: pytest.MonkeyPatch):
        """Mock run_server and capture the config it receives."""
        started = {}

        def mock_run_server(config):
            started["config"] = config

        monkeypatch.setattr("kbm.cli.start.run_server", mock_run_server)
        return started

    def test_starts_by_name(self, tmp_home: Path, capture_server: dict) -> None:
        """Starts server for named memory."""
        init_memory("srv", home=tmp_home)
        result = invoke("start", "srv", home=tmp_home)
        assert result.exit_code == 0
        assert capture_server["config"].settings.name == "srv"

    def test_transport_override(self, tmp_home: Path, capture_server: dict) -> None:
        """--transport overrides config value."""
        init_memory("srv", home=tmp_home)
        result = invoke("start", "srv", "-t", "http", home=tmp_home)
        assert result.exit_code == 0
        assert capture_server["config"].transport.value == "http"

    def test_host_port_override(self, tmp_home: Path, capture_server: dict) -> None:
        """--host/--port override config values."""
        init_memory("srv", home=tmp_home)
        result = invoke(
            "start", "srv", "-H", "192.168.1.1", "-p", "9000", home=tmp_home
        )
        assert result.exit_code == 0
        assert capture_server["config"].host == "192.168.1.1"
        assert capture_server["config"].port == 9000

    def test_path_override(self, tmp_home: Path, capture_server: dict) -> None:
        """--path overrides config value."""
        init_memory("srv", home=tmp_home)
        result = invoke("start", "srv", "--path", "/api/v1/mcp", home=tmp_home)
        assert result.exit_code == 0
        assert capture_server["config"].path == "/api/v1/mcp"

    def test_engine_override(self, tmp_home: Path, capture_server: dict) -> None:
        """--engine overrides config value."""
        init_memory("srv", home=tmp_home)
        result = invoke("start", "srv", "-e", "rag-anything", home=tmp_home)
        assert result.exit_code == 0
        assert capture_server["config"].engine.value == "rag-anything"

    def test_create_initializes_memory(
        self, tmp_home: Path, capture_server: dict
    ) -> None:
        """start initializes a new memory if it doesn't exist."""
        result = invoke("start", "new-mem", home=tmp_home)
        assert result.exit_code == 0
        assert capture_server["config"].settings.name == "new-mem"

        # Memory should now be queryable
        result = invoke("memory", "new-mem", home=tmp_home)
        assert result.exit_code == 0
