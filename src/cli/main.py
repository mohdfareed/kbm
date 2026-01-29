"""CLI entry point."""

import typer

from config import APP_NAME, DESCRIPTION

app = typer.Typer(name=APP_NAME, help=DESCRIPTION)


@app.callback()
def callback():
    """CLI application entry point."""
    pass


@app.command()
def test():
    """Test command to verify the CLI application."""
    print(f"Welcome to {APP_NAME}!")
