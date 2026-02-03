"""List command."""

from distro import name

from kbm.config import MemoryConfig, app_metadata

from .app import cli_app, console


@cli_app.command(name="list")
def list_memories() -> None:
    """List all memories."""
    found = False

    # Local
    try:
        cfg = MemoryConfig.load(name=None, config=None)
        console.print(f"[bold]Local:[/bold] {cfg.name} [dim]({cfg.engine.value})[/dim]")
        found = True
    except Exception:
        pass

    # Global
    if app_metadata.memories_path.exists():
        for path in sorted(app_metadata.memories_path.glob("*.yaml")):
            try:
                cfg = MemoryConfig.load(name=path.stem, config=None)
                marker = "✓" if cfg.data_path.exists() else "○"

                console.print(f"  {marker} {cfg.name:20} [dim]{cfg.engine.value}[/dim]")
                found = True
            except Exception:
                console.print(f"  ✗ {path.stem:20} [red]invalid[/red]")

    if not found:
        console.print("No memories found. Run: kbm init [name]")
