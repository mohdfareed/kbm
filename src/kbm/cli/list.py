"""List command."""

from kbm.config import MemoryConfig, app_settings

from . import app, console
from .helpers import print_invalid, print_status


@app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    data_dirs: list[str | None] = []
    found_any = False

    # All memories
    for path in sorted(app_settings.memories_path.iterdir()):
        found_any = True

        try:  # Load config from file
            memory = MemoryConfig.from_name(path.name)
            data_dirs.append(str(memory.settings.root.absolute()))
            print_status(memory)

        # Handle invalid config files
        except Exception as e:
            print_invalid(path.name, e)
            data_dirs.append(None)

    # No memories or data found
    if not found_any:
        console.print("[dim]No memories found. Use [bold]kbm init[/] to create one.[/]")
