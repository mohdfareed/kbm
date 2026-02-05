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
Backup by copying this directory.

## CLI

```
kbm <command> [options]

Commands:
  init [name]     Create memory
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

| Tool           | Description                       |
| -------------- | --------------------------------- |
| `query`        | Search knowledge base             |
| `insert`       | Add text                          |
| `insert_file`  | Add file (path or base64 content) |
| `delete`       | Remove record                     |
| `list_records` | List records                      |
| `info`         | Knowledge base metadata           |

## Docker

```sh
# Build
docker build -t kbm .

# Run (auto-creates memory if needed)
docker run -v kbm-data:/data -p 8000:8000 kbm
docker run -v kbm-data:/data -p 8000:8000 kbm my-memory  # custom name

# Debug logging
docker run -e KBM_DEBUG=1 -v kbm-data:/data -p 8000:8000 kbm
```

**docker-compose.yaml:**

```yaml
services:
  kbm:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - kbm-data:/data
    environment:
      - KBM_DEBUG=0

volumes:
  kbm-data:
```

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install deps
./scripts/run.sh --help  # run CLI
./scripts/check.sh       # lint, typecheck, test
```

## Architecture

**Engines** provide different retrieval strategies. Use `chat-history` for lightweight text storage,
`rag-anything` for semantic search over documents/images:

- `chat-history` - Simple JSON storage for conversations
- `rag-anything` - Multi-modal RAG with LightRAG
- `federation` - Aggregates queries across multiple memories, local and remote

**Canonical Storage** wraps all writable engines with a SQLite-backed persistence layer:

- Source of truth for all records and attachments
- Enables engine migration without data loss
- Allows rebuilding engine indexes from durable storage
- Uses async SQLAlchemy with aiosqlite

**Federation** enables querying multiple knowledge bases as one:

- Aggregates results from local memories and remote MCP servers
- Configures sources via:
  - `federation.memories` - names of local/global memories,
  - `federation.configs` - paths to config files, and
  - `federation.remotes` - MCP server URLs
- Read-only: can only query remote memories

## TODO

- [ ] **Attachments**: Support passing images/docs to `query` for enhanced context
- [ ] **Authorization (*Security*)**: Add API key support for HTTP server mode
  - Read/write scopes
  - API key generation and management commands
  - Key validation middleware for MCP requests
  - OAuth2 support for web interface
- [ ] **CI/CD (*Quality*)**: Automated testing, linting, and deployment pipelines
  - CI:
    - Tests with coverage on push and pull requests
    - Formatting, linting and type checking on all commits
  - CD:
    - Automated releases on tags
    - Publish to PyPI
    - Build and publish Docker images to GitHub Container Registry
