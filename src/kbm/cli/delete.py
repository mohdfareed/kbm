"""Delete command."""

import shutil

import typer

from kbm.config import MemoryConfig, app_settings

from . import MemoryNameArg, app, console
from .helpers import print_orphaned, print_summary


@app.command()
def delete(
    name: str = MemoryNameArg,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Permanently delete a memory and all its data."""
    cfg = None

    try:  # Load config from file
        cfg = MemoryConfig.from_name(name)
        data_path = cfg.data_path
        print_summary(cfg)

    # Load data if no config
    except FileNotFoundError:
        data_path = app_settings.data_root / name
        if not data_path.exists():
            raise  # Memory not found
        print_orphaned(data_path)

    # Confirm deletion
    if not yes:
        typer.confirm(
            f"Delete memory '{name}' and all its data?",
            default=False,
            abort=True,
        )

    # Delete config and data files
    if cfg and cfg.file_path.exists():
        cfg.file_path.unlink()
    if data_path.exists():
        shutil.rmtree(data_path)
    console.print(f"Deleted '{name}'.")
