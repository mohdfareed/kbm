# KBM - Knowledge Base Manager

Persistent memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Install

```sh
pipx install git+https://github.com/mohdfareed/kbm
```

## Quick Start

```sh
# Project memory (creates .kbm.yaml)
kbm init && kbm start

# Global memory
kbm init notes && kbm start notes
```

## Configuration

```yaml
# .kbm.yaml
name: my-project
engine: chat-history  # or rag-anything
```

Environment variables (`KBM_*`) override config. Loaded from `.kbm.env`, `.env`, or shell.

Data lives at `$KBM_HOME/data/<name>/` (default: platform data dir), never in your repo.

## CLI

```
kbm <command> [options]

Commands:
  init [name]     Create memory (local or global)
  start [name]    Start MCP server
  status [name]   Show configuration
  list            List all memories
  delete <name>   Delete global memory

Options:
  -c, --config    Config file path
  -d, --debug     Debug logging
  -v, --version   Show version
```

## MCP Tools

| Tool           | Description                |
| -------------- | -------------------------- |
| `query`        | Search knowledge base      |
| `insert`       | Add text                   |
| `insert_file`  | Add file (PDF, image, etc) |
| `delete`       | Remove record              |
| `list_records` | List records               |
| `info`         | Knowledge base metadata    |

## Docker

```sh
# Build locally
docker build -t kbm .

# Build from GitHub
docker build -t kbm https://github.com/mohdfareed/kbm.git

# Run with config file and persistent data
docker run -v ./config.yaml:/config.yaml:ro -v kbm-data:/data -p 8000:8000 kbm
```

**docker-compose.yaml:**

```yaml
services:
  kbm:
    build: https://github.com/mohdfareed/kbm.git
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/config.yaml:ro
      - kbm-data:/data
    environment:
      - KBM_RAG_ANYTHING__API_KEY=${OPENAI_API_KEY}

volumes:
  kbm-data:
```

```sh
docker compose up -d
```

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install deps
./scripts/run.sh --help  # run CLI
./scripts/check.sh       # lint, typecheck, test
```
