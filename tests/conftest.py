"""Shared test fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest

from app.config import APP_NAME


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir


@pytest.fixture
def reset_settings() -> Generator[None, None, None]:
    """Reset global settings singleton after test."""
    import app.config as config_module

    original = config_module._settings
    yield
    config_module._settings = original


@pytest.fixture
def reset_engine_registry() -> Generator[None, None, None]:
    """Reset engine registry after test."""
    from engines import _registry

    original = _registry.copy()
    yield
    _registry.clear()
    _registry.update(original)


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove env vars for clean config tests."""
    env_vars = {
        k: v for k, v in os.environ.items() if k.startswith(f"{APP_NAME.upper()}_")
    }
    for k in env_vars:
        del os.environ[k]
    yield
    os.environ.update(env_vars)
