"""Delete command."""

import shutil

import typer

from kbm.config import MemoryConfig, app_settings

from . import app, console


@app.command()
def delete(
    name: str = typer.Argument(..., help="Local or global memory name."),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation."),
    keep_data: bool = typer.Option(False, "--keep-data", help="Keep data directory."),
) -> None:
    """Delete a global memory."""
    cfg = None
    msg = None

    try:
        cfg = MemoryConfig.from_name(name=name)
        data_path = cfg.data_path
    except FileNotFoundError:
        data_path = app_settings.data_root / name  # orphaned data path

    # Confirmation message
    data_path_exists = data_path.exists()
    if cfg and data_path_exists and keep_data:
        msg = f"Delete [bold]{name}[/bold] config? [dim](data is preserved)[/dim]"
    elif cfg and data_path_exists and not keep_data:
        msg = f"Delete [bold]{name}[/bold] and all its data?"
    elif cfg and not data_path_exists:
        msg = f"Delete [bold]{name}[/bold] config? [dim](data not found)[/dim]"
    elif not cfg and data_path_exists and not keep_data:
        msg = f"Delete [bold]{name}[/bold] data? [dim](config not found)[/dim]"

    # Handle not found cases
    elif not cfg and data_path_exists and keep_data:
        console.print(f"Memory [bold]{name}[/bold] not found.")
        console.print(f"Can only delete data but keep_data is set.")
        raise typer.Exit(1)
    elif not cfg and not data_path_exists:
        console.print(f"Memory [bold]{name}[/bold] not found.")
        console.print(f"Config and data do not exist.")
        raise typer.Exit(1)

    if not msg or (not cfg and not data_path_exists):
        raise RuntimeError("Unexpected state in delete command.", cfg, data_path)

    if not yes:
        console.print(msg)
        typer.confirm("Continue?", default=False, abort=True)

    if cfg:
        cfg.file_path.unlink()
        console.print(f"[green]✓[/green] Deleted config: {cfg.file_path}")

    if data_path_exists and not keep_data:
        shutil.rmtree(data_path)
        console.print(f"[green]✓[/green] Deleted data: {data_path}")
