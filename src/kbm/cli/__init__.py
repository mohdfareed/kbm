"""CLI package."""

__all__ = ["app", "console", "err_console", "main"]

import logging
import sys

import typer
from rich.console import Console
from rich.logging import RichHandler

from kbm.config import app_settings

# Separate consoles for stdout/stderr (enables proper piping)
console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name=app_settings.name,
    help=app_settings.description,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",  # Enable rich markup in help text
)

# App logger (not root - avoids library noise)
log = logging.getLogger("kbm")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{app_settings.name} {app_settings.version}")
        raise typer.Exit(code=0)


@app.callback()
def callback(
    debug: bool = typer.Option(
        app_settings.debug, "-d", "--debug", help="Enable debug logging ($KBM_DEBUG)."
    ),
    version: bool = typer.Option(
        False,
        "-v",
        "--version",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Persistent memory for LLMs via MCP."""
    app_settings.debug = debug or app_settings.debug

    level = logging.DEBUG if app_settings.debug else logging.INFO
    handler = RichHandler(
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
    logging.getLogger("fastmcp").handlers = [handler]
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)


@app.command()
def home() -> None:
    """Print application home directory."""
    typer.echo(app_settings.data_root)


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except Exception as e:
        if app_settings.debug:
            err_console.print_exception()
        else:
            err_console.print(f"[bold red]Error:[/] {e}")
        raise sys.exit(1)


# Register commands (order determines help display)
# isort: off
from kbm.cli import init, start, status, list, delete  # noqa: E402
# isort: on
