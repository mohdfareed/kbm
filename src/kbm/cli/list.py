"""List command."""

from kbm.config import MemoryConfig, app_settings

from . import app, console
from .helpers import print_invalid, print_status


@app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    found_any = False

    # All memories
    for path in app_settings.memories:
        found_any = True

        try:  # Load config from file
            memory = MemoryConfig.from_name(path.name)
            print_status(memory)

        # Handle invalid config files
        except Exception as e:
            print_invalid(path.name, e)

    # No memories or data found
    if not found_any:
        console.print("[dim]No memories found. Use [bold]kbm init[/] to create one.[/]")
