"""CLI package."""

__all__ = ["app", "main"]

import logging

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from kbm.config import app_settings

console = Console()
app = typer.Typer(
    name=app_settings.name,
    help=app_settings.description,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"{app_settings.name} {app_settings.version}")
        raise typer.Exit(code=0)


@app.callback()
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


@app.command()
def info() -> None:
    """Show application information."""
    info = "\n".join(
        [
            f"[dim]Version:[/dim]  {app_settings.version}",
            f"[dim]Home:[/dim]     {app_settings.home}",
            f"[dim]Memories:[/dim] {app_settings.memories_path}",
            f"[dim]Data:[/dim]     {app_settings.data_root}",
        ]
    )
    console.print(
        Panel(info, title=app_settings.name, subtitle=app_settings.description)
    )


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except typer.Abort:
        console.print("[yellow]Aborted.[/yellow]")
        raise SystemExit(1) from None
    except Exception as e:
        if logging.root.level == logging.DEBUG:
            console.print_exception()
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from None


# Register commands
from kbm.cli import delete, init, list, start, status  # noqa: E402
