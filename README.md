# KBM — Knowledge Base Manager

KBM is a unified memory system that any LLM tool can read from and write to via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Requirements

- Python 3.12+

## Installation

```sh
pipx install kbm
```

## Development

### Requirements

- [`uv`](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/bootstrap.sh
uv run kbm
```

**Useful `uv` commands:**

- `uv run kbm <args>` - Run KBM.
- `uv add [--dev] <pkg>` - Add a new dependency.
- `uv sync` - Sync dependencies from lock file.
- `uv lock` - Regenerate lock file.

## License

[MIT](LICENSE)
