"""CLI helpers: logging and display utilities."""

__all__ = [
    "format_config",
    "print_invalid",
    "print_status",
    "print_summary",
    "setup_file_logging",
    "setup_logging",
]

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler
from rich.panel import Panel

from kbm.config import MemoryConfig, Transport, app_settings


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


def format_config(data: dict) -> list[str]:
    """Format a config dict into aligned Rich-markup lines."""
    lines: list[str] = []

    # Separate top-level scalars from nested sections
    scalars: list[tuple[str, str]] = []
    sections: list[tuple[str, list[tuple[str, str]]]] = []

    for key, value in data.items():
        if isinstance(value, dict):
            items = [(k, str(v)) for k, v in value.items()]
            if items:
                sections.append((key, items))
        else:
            scalars.append((key, str(value)))

    # Top-level scalars
    if scalars:
        w = max(len(k) for k, _ in scalars)
        lines += [f"[dim]{k:<{w}}[/]  {v}" for k, v in scalars]

    # Nested sections
    for section, items in sections:
        lines.append(f"[dim]{section}:[/]")
        w = max(len(k) for k, _ in items)
        lines += [f"  [dim]{k:<{w}}[/]  {v}" for k, v in items]

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
    header = f"[bold]Config:[/] {memory.settings.config_file}"

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
