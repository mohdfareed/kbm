"""CLI helpers: logging and display utilities."""

__all__ = [
    "dump_display",
    "format_config",
    "print_invalid",
    "print_status",
    "print_summary",
    "setup_file_logging",
    "setup_logging",
]

import logging
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler
from rich.panel import Panel

from kbm.config import AuthProvider, Engine, MemoryConfig, Transport, app_settings


def setup_logging() -> None:
    """Configure logging."""
    from . import err_console

    level = logging.DEBUG if app_settings.debug else logging.INFO
    handler = RichHandler(
        level=level,
        console=err_console,
        show_time=app_settings.debug,
        show_path=app_settings.debug,
        rich_tracebacks=True,
        markup=True,
        keywords=[],  # Highlight keywords
    )
    handler.setFormatter(logging.Formatter("[dim]%(name)s:[/] %(message)s"))

    logging.root.setLevel(level)
    logging.root.addHandler(handler)

    # Logging levels for libraries
    logging.getLogger("fastmcp").handlers = [*logging.root.handlers]
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)


def setup_file_logging(log_file: Path) -> None:
    """Configure file logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )

    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logging.root.addHandler(file_handler)

    # Stamp the log with a session start message to separate runs
    # Use a temporary logger to avoid affecting other handlers
    session_logger = logging.getLogger(f"{app_settings.name}.session")
    session_logger.addHandler(file_handler)
    session_logger.setLevel(logging.INFO)
    session_logger.propagate = False
    session_logger.info("--- New Session ---")


def dump_display(memory: MemoryConfig, active_only: bool = True) -> dict:
    """Build a display dict for a memory config, preserving Enum instances.

    When ``active_only`` is True, only include sections relevant to the
    currently chosen engine, transport, and auth provider.  When False,
    include every field (useful as a full reference/config template).
    """
    data = memory.model_dump(mode="python", exclude_computed_fields=True)

    if not active_only:
        return data

    result: dict = {}

    # Core choices (always shown)
    result["instructions"] = memory.instructions
    result["engine"] = memory.engine
    result["transport"] = memory.transport
    result["auth"] = memory.auth

    # Engine-specific sub-config
    match memory.engine:
        case Engine.RAG_ANYTHING:
            result["rag_anything"] = data["rag_anything"]
        case Engine.MEM0:
            result["mem0"] = data["mem0"]

    # Transport-specific (host/port only matter for HTTP)
    if memory.transport == Transport.HTTP:
        result["host"] = memory.host
        result["port"] = memory.port

    # Auth-specific sub-config
    if memory.auth != AuthProvider.NONE:
        auth_key = f"{memory.auth.value}_auth"
        if auth_key in data:
            result[auth_key] = data[auth_key]

    return result


def format_config(data: dict, indent: int = 0) -> list[str]:
    """Format a config dict into aligned Rich-markup lines, recursively."""
    lines: list[str] = []
    pad = "  " * indent

    scalars: list[tuple[str, str, str]] = []  # (key, value, choices)
    sections: list[tuple[str, dict]] = []

    for key, value in data.items():
        if isinstance(value, dict):
            sections.append((key, value))
        else:
            if isinstance(value, Enum):
                choices = f"[dim]({', '.join(e.value for e in type(value))})[/]"
                scalars.append((key, value.value, choices))
            else:
                scalars.append((key, str(value), ""))

    if scalars:
        kw = max(len(k) for k, _, _ in scalars)
        for k, v, choices in scalars:
            suffix = f"  {choices}" if choices else ""
            lines.append(f"{pad}[dim]{k:<{kw}}[/]  {v}{suffix}")

    for section, items in sections:
        lines.append(f"{pad}[dim]{section}:[/]")
        lines += format_config(items, indent + 1)

    return lines


def print_status(memory: MemoryConfig) -> None:
    """Print one-line memory status: icon, name, file, engine, transport."""
    from . import console

    console.print(
        f"[bold]{memory.settings.name}[/]"
        f" • [dim]{memory.engine.value}[/]"
        f" • [dim]{_transport_label(memory)}[/]"
    )


def print_invalid(name: str, error: Exception) -> None:
    """Print one-line status for an invalid/unreadable config."""
    from . import console

    console.print(f"[red]●[/] [dim]{name}[/] • [dim]invalid: {error}[/]")


def print_summary(memory: MemoryConfig) -> None:
    """Print a Panel with memory name, engine, transport, and paths."""
    from . import console

    title = (
        f"[bold]{memory.settings.name}[/]"
        f" • [dim]{memory.engine.value}[/]"
        f" • [dim]{_transport_label(memory)}[/]"
    )
    header = f"[bold]Data:[/] {memory.settings.root}"

    console.print(
        Panel(
            header,
            title=title,
            title_align="left",
            border_style="dim",
        )
    )


def _transport_label(memory: MemoryConfig) -> str:
    """Human-readable transport string."""
    match memory.transport:
        case Transport.STDIO:
            return "stdio"
        case Transport.HTTP:
            return f"http://{memory.host}:{memory.port}"
        case _:
            return memory.transport.value
