"""List command."""

from kbm.config import MemoryConfig, app_settings

from . import app, console


@app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    data_dirs = []

    # Local memories
    for path in app_settings.local_config_files():
        try:
            cfg = MemoryConfig.from_config(path)
            _print_memory(cfg)
            data_dirs.append(cfg.data_path)

        except Exception:
            console.print(
                f"[red]●[/red] [bold]{path.stem}[/bold] [red]• local • invalid[/red]"
            )
            data_dirs.append(None)

    # Global memories
    for path in app_settings.global_config_files():
        try:
            cfg = MemoryConfig.from_config(path)
            _print_memory(cfg)
            data_dirs.append(cfg.data_path)

        except Exception:
            console.print(
                f"[red]●[/red] [bold]{path.stem}[/bold] [red]• global • invalid[/red]"
            )
            data_dirs.append(None)

    # Orphaned data directories
    for path in app_settings.data_root.iterdir():
        if path not in data_dirs:
            console.print(
                f"[blue]●[/blue] [bold]{path.name}[/bold] [dim]• data • orphaned[/dim]"
            )

    if not data_dirs:
        console.print("No memories found.")
        console.print("Use [bold]kbm init[/bold] to create a new memory.")


def _print_memory(cfg: MemoryConfig) -> None:
    has_data = cfg.data_path.exists()
    icon = "[green]●[/green]" if has_data else "[yellow]●[/yellow]"
    if cfg.is_global:
        console.print(
            f"{icon} [bold]{cfg.name}[/bold] [dim]• global • {cfg.engine.value}[/dim]"
        )
    else:
        console.print(
            f"{icon} [bold]{cfg.name}[/bold] [dim]• local • {cfg.engine.value}[/dim]"
        )
