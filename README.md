# KBM — Knowledge Base Manager

KBM is a unified memory system that any LLM tool can read from and write to via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Requirements

- Python 3.12+
- [`pipx`](https://pipxproject.github.io/pipx/) or any pip-compatible installer

### Development

- [`uv`](https://docs.astral.sh/uv/)

## Installation

```sh
pipx install https://github.com/mohdfareed/kbm
kbm --help
```

### Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh # set up development environment
./scripts/run.sh --help
```

## License

[MIT](LICENSE)
