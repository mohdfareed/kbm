"""CLI helpers: logging and display utilities."""

__all__ = [
    "format_config",
    "print_invalid",
    "print_orphaned",
    "print_status",
    "print_summary",
    "setup_file_logging",
    "setup_logging",
]

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

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
    handler.setFormatter(logging.Formatter("[dim]%(name)s:[/dim] %(message)s"))

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


def print_status(cfg: MemoryConfig) -> None:
    """Print one-line memory status: icon, file, name, engine."""
    from . import console

    match cfg.transport:
        case Transport.STDIO:
            transport = "stdio"
        case Transport.HTTP:
            transport = f"http://{cfg.host}:{cfg.port}"
        case _:
            transport = cfg.transport.value

    icon = "[green]●[/green]" if cfg.data_path.exists() else "[yellow]●[/yellow]"
    console.print(
        f"{icon} [bold]{cfg.name}[/bold]"
        f" • [dim]{cfg.file_path.name}[/dim]"
        f" • [dim]{cfg.engine.value}[/dim] • [dim]{transport}[/dim]"
    )


def print_invalid(config_file: Path, error: Exception) -> None:
    """Print one-line status for an invalid/unreadable config."""
    from . import console

    console.print(
        f"[red]●[/red] [dim]{config_file.name}[/dim] • [dim]invalid: {error}[/dim]"
    )


def print_orphaned(data_dir: Path) -> None:
    """Print one-line status for an orphaned data directory."""
    from . import console

    console.print(
        f"[yellow]●[/yellow] [bold]{data_dir.name}[/bold] • [dim]orphaned[/dim]"
    )


def format_config(data: dict, prefix: str = "") -> list[str]:
    """Flatten a (possibly nested) config dict into `key=value` lines."""
    lines: list[str] = []
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            lines.extend(format_config(value, full_key))
        else:
            lines.append(f"{full_key}={value}")
    return lines


def print_summary(cfg: MemoryConfig) -> None:
    """Print status line plus config and data paths."""
    from . import console

    print_status(cfg)
    console.print(f"  [dim]Config:[/dim] {cfg.file_path}")
    console.print(f"  [dim]Data:[/dim]   {cfg.data_path}")
