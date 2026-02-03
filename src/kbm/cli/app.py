"""CLI application."""

import logging

import typer
from rich.console import Console
from rich.logging import RichHandler

from kbm.config import app_metadata

console = Console()
cli_app = typer.Typer(
    name=app_metadata.name,
    help=app_metadata.description,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"{app_metadata.name} {app_metadata.version}")
        raise typer.Exit(code=0)


@cli_app.callback()
def callback(
    debug: bool = typer.Option(False, "-d", "--debug", help="Debug logging."),
    version: bool = typer.Option(
        False,
        "-v",
        "--version",
        help="Show version.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    if debug:
        logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(RichHandler(console=console))


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        cli_app(prog_name=prog_name)
    except typer.Abort:
        console.print("[dim]Aborted.[/dim]")
        raise SystemExit(1) from None
    except Exception as e:
        if logging.root.level == logging.DEBUG:
            console.print_exception()
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from None


# Register commands
from kbm.cli import delete, init, list, start, status  # noqa: E402
