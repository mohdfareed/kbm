"""CLI entry point."""

import typer
from cli import APP_NAME


app = typer.Typer()


@app.callback()
def callback():
    """Main entry point for the CLI application."""

@app.command()
def test():
    """Test command to verify the CLI application."""
    print(f"Welcome to {APP_NAME}!")
