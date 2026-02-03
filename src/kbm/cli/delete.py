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

    msg = f"Delete '{name}'?"
    if cfg.data_path.exists() and not keep_data:
        msg += f" This will also delete: {cfg.data_path}"

    if not yes and not typer.confirm(msg):
        raise typer.Abort()

    cfg.file_path.unlink()
    console.print(f"Deleted {cfg.file_path}")

    if cfg.data_path.exists() and not keep_data:
        shutil.rmtree(cfg.data_path)
        console.print(f"Deleted {cfg.data_path}")
