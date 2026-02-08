"""Shared test fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from repo's .env file by changing to temp directory."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def tmp_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Set up temporary KBM home directory."""
    from kbm.config import app_settings

    original_home = app_settings.home

    home = tmp_path / "kbm-home"
    home.mkdir()
    (home / "memories").mkdir()
    (home / "data").mkdir()
    app_settings.home = home

    yield home

    app_settings.home = original_home


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove KBM env vars for clean config tests."""
    for k in list(os.environ):
        if k.startswith("KBM_"):
            monkeypatch.delenv(k)
