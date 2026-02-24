"""CLI command tests.

Tests compose CLI commands to verify behaviors (init → list → status → start
→ delete) rather than asserting internal file paths or directory layouts.
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

    def test_init_and_list(self, tmp_home: Path) -> None:
        """Initialized memory appears in list."""
        init_memory("my-mem")
        result = runner.invoke(app, ["list"])
        assert "my-mem" in result.stdout

    def test_init_and_status(self, tmp_home: Path) -> None:
        """Initialized memory is queryable via status."""
        init_memory("my-mem")
        result = runner.invoke(app, ["status", "my-mem"])
        assert result.exit_code == 0
        assert "my-mem" in result.stdout

    def test_default_name_is_cwd(self, tmp_home: Path) -> None:
        """No name argument uses current directory name."""
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Default name was resolved at import time from cwd
        from kbm.cli import MemoryNameArg

        default_name = MemoryNameArg.default
        result = runner.invoke(app, ["status", default_name])
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
        """--engine is reflected in status output."""
        init_memory("rag-mem", engine="rag-anything")
        result = runner.invoke(app, ["status", "rag-mem", "--full"])
        assert result.exit_code == 0
        assert "rag-anything" in result.stdout


# -- Delete -------------------------------------------------------------------


class TestDelete:
    """Test 'kbm delete' command."""

    def test_delete_removes_from_list(self, tmp_home: Path) -> None:
        """Deleted memory disappears from list."""
        init_memory("to-delete")
        result = runner.invoke(app, ["delete", "to-delete", "--yes"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["list"])
        assert "to-delete" not in result.stdout

    def test_nonexistent_fails(self, tmp_home: Path) -> None:
        """Deleting nonexistent memory fails."""
        result = runner.invoke(app, ["delete", "ghost", "--yes"])
        assert result.exit_code != 0

    def test_confirms_by_default(self, tmp_home: Path) -> None:
        """Prompts for confirmation without --yes, 'n' aborts."""
        init_memory("confirm-test")
        result = runner.invoke(app, ["delete", "confirm-test"], input="n\n")
        assert result.exit_code != 0

        # Memory still exists
        result = runner.invoke(app, ["status", "confirm-test"])
        assert result.exit_code == 0


# -- List ---------------------------------------------------------------------


class TestList:
    """Test 'kbm list' command."""

    def test_empty(self, tmp_home: Path) -> None:
        """Empty state shows helpful message."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No memories found" in result.stdout

    def test_shows_all_memories(self, tmp_home: Path) -> None:
        """Lists all initialized memories."""
        init_memory("alpha")
        init_memory("beta")

        result = runner.invoke(app, ["list"])
        assert "alpha" in result.stdout
        assert "beta" in result.stdout


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

        # Memory should now be listed
        result = invoke("list", home=tmp_home)
        assert "new-mem" in result.stdout


# -- Status -------------------------------------------------------------------


class TestStatus:
    """Test 'kbm status' command."""

    def test_shows_name(self, tmp_home: Path) -> None:
        """Status displays memory name."""
        init_memory("my-mem")
        result = runner.invoke(app, ["status", "my-mem"])
        assert result.exit_code == 0
        assert "my-mem" in result.stdout

    def test_nonexistent_fails(self, tmp_home: Path) -> None:
        """Status for nonexistent memory fails."""
        result = runner.invoke(app, ["status", "ghost"])
        assert result.exit_code != 0
