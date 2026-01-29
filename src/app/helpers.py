"""Helper functions and utilities."""

from collections.abc import Iterable
from pathlib import Path


def find_file(names: Iterable[str]) -> Path | None:
    """Search for file progressively up the directory tree."""
    current = Path.cwd().resolve()

    while True:
        for name in names:
            path = current / name
            try:
                if path.is_file():
                    return path
            except PermissionError:
                return None

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None
