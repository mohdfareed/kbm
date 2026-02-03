"""Enable `python -m kbm`."""

from kbm import app
from kbm.config import app_metadata

if __name__ == "__main__":
    app(prog_name=app_metadata.name)
