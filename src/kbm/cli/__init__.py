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
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug logging."),
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
    # Configure logging once
    if not log.handlers:
        handler = RichHandler(
            console=err_console,
            show_time=debug,
            show_path=debug,
            rich_tracebacks=True,
        )
        log.addHandler(handler)
    log.setLevel(logging.DEBUG if debug else logging.WARNING)


@app.command()
def home() -> None:
    """Print application home directory."""
    typer.echo(app_settings.data_root)


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except KeyboardInterrupt:
        err_console.print("[dim]Interrupted[/dim]")
        sys.exit(130)
    except typer.Abort:
        err_console.print("[yellow]Aborted[/yellow]")
        sys.exit(1)
    except Exception as e:
        if log.level == logging.DEBUG:
            err_console.print_exception()
        else:
            err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# Register commands (order determines help display)
# isort: off
from kbm.cli import init, start, status, list, delete  # noqa: E402
# isort: on
