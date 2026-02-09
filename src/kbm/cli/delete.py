"""Delete command."""

import shutil

import typer

from kbm.config import MemoryConfig

from . import MemoryNameArg, app, console
from .helpers import print_summary


@app.command()
def delete(
    name: str = MemoryNameArg,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Permanently delete a memory and all its data."""
    memory = MemoryConfig.from_name(name)
    print_summary(memory)

    if not yes:
        typer.confirm(
            f"Delete memory '{name}' and all its data?",
            default=False,
            abort=True,
        )

    shutil.rmtree(memory.settings.root)
    console.print(f"Deleted '{name}'.")
