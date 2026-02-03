"""Delete command."""

import shutil

import typer

from kbm.config import MemoryConfig

from .app import cli_app, console


@cli_app.command()
def delete(
    name: str = typer.Argument(..., help="Global memory name."),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation."),
    keep_data: bool = typer.Option(False, "--keep-data", help="Keep data directory."),
) -> None:
    """Delete a global memory."""
    cfg = MemoryConfig.load(name=name, config=None)
    has_data = cfg.data_path.exists()

    # Confirmation message
    if has_data and not keep_data:
        msg = f"Delete [bold]{name}[/bold] and all its data?"
    elif has_data:
        msg = f"Delete [bold]{name}[/bold] config? [dim](data will be kept)[/dim]"
    else:
        msg = f"Delete [bold]{name}[/bold]?"

    if not yes:
        console.print(msg)
        if not typer.confirm("Continue?", default=False):
            raise typer.Abort()

    cfg.file_path.unlink()
    console.print(f"[green]✓[/green] Deleted config: {cfg.file_path}")

    if has_data and not keep_data:
        shutil.rmtree(cfg.data_path)
        console.print(f"[green]✓[/green] Deleted data: {cfg.data_path}")
