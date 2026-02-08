"""List command."""

from kbm.config import MemoryConfig, app_settings

from . import app, console
from .helpers import print_invalid, print_orphaned, print_status


@app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    data_dirs: list[str | None] = []
    found_any = False

    # All memories
    for path in app_settings.memories:
        found_any = True

        try:  # Load config from file
            cfg = MemoryConfig.from_file(path)
            data_dirs.append(str(cfg.data_path.absolute()))
            print_status(cfg)

        # Handle invalid config files
        except Exception as e:
            print_invalid(path, e)
            data_dirs.append(None)

    # Orphaned data directories
    for path in app_settings.data:
        if str(path.absolute()) not in data_dirs:
            found_any = True
            print_orphaned(path)

    # No memories or data found
    if not found_any:
        console.print("[dim]No memories found. Use [bold]kbm init[/] to create one.[/]")
