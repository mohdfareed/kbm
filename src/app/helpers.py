"""Helper functions and utilities."""

__all__ = [
    "LazyGroup",
    "configure_logging",
    "console",
    "find_file",
    "get_docstring",
    "make_sync_command",
    "settings_to_env",
    "status_spinner",
]

import logging
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

import click
import typer
from rich.console import Console
from rich.logging import RichHandler
from typer.core import TyperGroup  # type: ignore[import-untyped]

# MARK: CLI utilities

console = Console()
_debug_mode = False


def configure_logging(debug: bool) -> None:
    """Configure logging for CLI commands."""
    global _debug_mode
    _debug_mode = debug

    if not debug:
        logging.disable(logging.CRITICAL)
        return

    # Configure root logger to capture all library logs
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(RichHandler(console=console))


@contextmanager
def status_spinner(message: str):
    """Show spinner unless in debug mode."""
    if _debug_mode:
        yield
        return

    with console.status(message):
        yield


# MARK: File utilities


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


def settings_to_env(data: dict, prefix: str) -> list[str]:
    """Convert settings dict to environment variable lines."""
    lines: list[str] = []
    for key, value in data.items():
        env_key = f"{prefix}_{key}".upper()
        if isinstance(value, dict):
            lines.extend(settings_to_env(value, env_key))
        elif value is not None:
            lines.append(f"{env_key}={value}")
    return lines


# MARK: Tool/command helpers


def get_docstring(method) -> str:
    """Extract first line of docstring for tool/command description."""
    return (method.__doc__ or "").split("\n")[0].strip()


def make_sync_command(async_method, get_instance: Callable):
    """Create a sync CLI command from an async method.

    Args:
        async_method: The async method to wrap (unbound, from class).
        get_instance: Callable that returns the object instance at runtime.

    Returns:
        A sync function with the same signature that Typer can introspect.
    """
    import asyncio
    import inspect
    from functools import wraps

    method_name = async_method.__name__
    sig = inspect.signature(async_method)

    # Build new signature excluding 'self'
    new_params = [p for name, p in sig.parameters.items() if name != "self"]
    new_sig = sig.replace(parameters=new_params)

    @wraps(async_method)
    def sync_wrapper(*args, **kwargs):
        with status_spinner("Processing..."):
            instance = get_instance()
            result = asyncio.run(getattr(instance, method_name)(*args, **kwargs))
        console.print(result)

    # Typer reads __signature__ to determine CLI arguments
    sync_wrapper.__signature__ = new_sig  # type: ignore[attr-defined]
    return sync_wrapper


# MARK: Lazy loading CLI group


class LazyGroup(TyperGroup):  # type: ignore[misc]
    """Typer group that defers subcommand creation until invocation.

    Register lazy commands via `lazy_commands` dict mapping name -> factory.
    Factory is called only when the command is invoked (after config loads).
    """

    lazy_commands: ClassVar[dict[str, Callable]] = {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        return [*base, *self.lazy_commands.keys()]

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self.lazy_commands:
            return self._invoke_lazy(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _invoke_lazy(self, name: str) -> click.Command:
        """Invoke lazy command factory (ensures config is loaded first)."""
        from app.config import get_settings, init_settings

        try:
            get_settings()
        except RuntimeError:
            init_settings(None)

        factory = self.lazy_commands[name]
        return typer.main.get_command(factory())
