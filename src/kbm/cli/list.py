"""List command."""

from kbm.config import MemoryConfig, app_settings

from . import app, console


@app.command(name="list")
def list_memories() -> None:
    """List all memories.

    - [green]●[/green] Memory with data
    - [blue]●[/blue] The local (active) memory
    - [yellow]●[/yellow] Memory without data or orphaned data
    - [red]●[/red] Invalid memory configuration
    """

    data_dirs: list[str | None] = []
    found_any = False

    # Local memories
    is_first = True
    for path in app_settings.local_config_files():
        found_any = True

        try:
            cfg = MemoryConfig.from_config(path)
            data_dirs.append(str(cfg.data_path))

            _print_memory(cfg, is_first)
            is_first = False

        except Exception:
            console.print(
                f"[red]●[/red] [bold]{path.stem}[/bold] [dim]• local • invalid[/dim]"
            )
            data_dirs.append(None)

    # Global memories
    for path in app_settings.global_config_files():
        found_any = True

        try:
            cfg = MemoryConfig.from_config(path)
            _print_memory(cfg)
            data_dirs.append(str(cfg.data_path))

        except Exception:
            console.print(
                f"[red]●[/red] [bold]{path.stem}[/bold] [dim]• global • invalid[/dim]"
            )
            data_dirs.append(None)

    # Orphaned data directories
    for path in app_settings.data_root.iterdir():
        if str(path) not in data_dirs:
            found_any = True

            engines = [p.name for p in path.iterdir() if p.is_dir()]
            console.print(
                f"[yellow]●[/yellow] [bold]{path.name}[/bold] [dim]• data "
                f"• {'|'.join(engines)}[/dim]"
            )

    if not found_any:
        console.print(
            "[dim]No memories found. Run [bold]kbm init[/bold] to create one.[/dim]"
        )


def _print_memory(cfg: MemoryConfig, first=False) -> None:
    has_data = cfg.data_path.exists()

    icon = "[blue]●[/blue]" if first else "[green]●[/green]"
    icon = icon if has_data else "[yellow]●[/yellow]"
    location = "local" if not cfg.is_global else "global"

    console.print(
        f"{icon} [bold]{cfg.name}[/bold] [dim]• {location} • {cfg.engine.value}[/dim]"
    )
