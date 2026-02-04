"""Delete command."""

import shutil

import typer

from kbm.config import MemoryConfig, app_settings

from . import app, console


@app.command()
def delete(
    name: str = typer.Argument(..., help="Memory name to delete."),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation."),
    keep_data: bool = typer.Option(False, "--keep-data", help="Keep data directory."),
) -> None:
    """Delete a memory."""
    cfg = None
    data_path = app_settings.data_root / name

    try:
        cfg = MemoryConfig.from_name(name)
        data_path = cfg.data_path
    except FileNotFoundError:
        pass  # Try orphaned data

    has_config = cfg is not None
    has_data = data_path.exists()

    if not has_config and not has_data:
        raise FileNotFoundError(name)

    if not has_config and keep_data:
        raise typer.BadParameter("No config found and --keep-data is set.")

    # Build confirmation message
    if has_config and has_data and not keep_data:
        msg = f"Delete [bold]{name}[/bold] config and data?"
    elif has_config and has_data and keep_data:
        msg = f"Delete [bold]{name}[/bold] config? [dim](keeping data)[/dim]"
    elif has_config and not has_data:
        msg = f"Delete [bold]{name}[/bold] config? [dim](no data found)[/dim]"
    else:  # not has_config and has_data
        msg = f"Delete orphaned data for [bold]{name}[/bold]?"

    if not yes:
        console.print(msg)
        typer.confirm("Continue?", default=False, abort=True)

    if has_config and cfg:
        cfg.file_path.unlink()
        console.print(f"[green]✓[/green] Deleted config")

    if has_data and not keep_data:
        shutil.rmtree(data_path)
        console.print(f"[green]✓[/green] Deleted data")
