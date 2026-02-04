"""Enable `python -m kbm`."""

from kbm.cli import main as app
from kbm.config import app_settings

if __name__ == "__main__":
    app(prog_name=app_settings.name)
