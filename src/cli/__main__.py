"""Package entry point."""

from cli.main import app
from config import APP_NAME

app(prog_name=APP_NAME)
