# KBM — Knowledge Base Manager

Unified memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Install

```sh
pipx install git+https://github.com/mohdfareed/kbm
```

## Usage

```sh
kbm start           # start MCP server
kbm memory --help   # knowledge base operations
kbm config          # show configuration
kbm version         # show version
```

## Configuration

Settings are loaded from environment variables or a `.env` file (searched up from cwd).

```sh
kbm config > .env   # export current config
```

## Development

Requires [`uv`](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh
./scripts/run.sh --help
```

## License

[MIT](LICENSE)
