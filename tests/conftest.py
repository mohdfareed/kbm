"""Shared test fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest

from app.config import APP_NAME, get_settings
from app.config import reset_settings as _reset_settings


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir


@pytest.fixture
def reset_settings() -> Generator[None, None, None]:
    """Reset global settings singleton after test."""
    try:
        original = get_settings()
    except RuntimeError:
        original = None
    yield
    _reset_settings(original)


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove env vars for clean config tests."""
    env_vars = {
        k: v for k, v in os.environ.items() if k.startswith(f"{APP_NAME.upper()}_")
    }
    for k in env_vars:
        del os.environ[k]
    yield
    # Restore env vars
    os.environ.update(env_vars)
