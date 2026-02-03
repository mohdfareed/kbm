"""List command."""

from kbm.config import MemoryConfig, app_metadata

from .app import cli_app, console


@cli_app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    found = False

    # Local memory
    try:
        cfg = MemoryConfig.load(name=None, config=None)
        has_data = cfg.data_path.exists()
        icon = "[green]●[/green]" if has_data else "[yellow]○[/yellow]"
        console.print(
            f"{icon} [bold]{cfg.name}[/bold] [dim]• local • {cfg.engine.value}[/dim]"
        )
        found = True
    except Exception:
        pass

    # Global memories
    if app_metadata.memories_path.exists():
        for path in sorted(app_metadata.memories_path.glob("*.yaml")):
            try:
                cfg = MemoryConfig.load(name=path.stem, config=None)
                has_data = cfg.data_path.exists()
                icon = "[green]●[/green]" if has_data else "[yellow]○[/yellow]"
                console.print(
                    f"{icon} [bold]{cfg.name}[/bold] [dim]• {cfg.engine.value}[/dim]"
                )
                found = True
            except Exception:
                console.print(
                    f"[red]✗[/red] [bold]{path.stem}[/bold] [red]• invalid config[/red]"
                )
                found = True

    if not found:
        console.print("No memories found.")
        console.print("Use [bold]kbm init[/bold] to create a new memory.")
