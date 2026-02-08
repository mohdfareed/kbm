# KBM - Knowledge Base Manager

Persistent memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Install

```sh
uv tool install git+https://github.com/mohdfareed/kbm
pipx install git+https://github.com/mohdfareed/kbm
```

## Quick Start

```sh
kbm init && kbm start # defaults to cwd name
kbm init notes && kbm start notes
```

## Configuration

* Environment variables (`KBM_*`) override config. Loaded from `.env`, or shell.
* Data lives at `$KBM_HOME` (default: platform data dir).
  * `kbm home` displays the current home directory.
  * Backup/migrate by copying this directory.
* `kbm status <name> --full` shows all config options with defaults.

## Features

**Engines** provide different retrieval strategies:

- `chat-history` - Simple JSON storage for conversations
- `rag-anything` - Multi-modal RAG with LightRAG

**Canonical Storage** wraps all writable engines with a SQLite-backed persistence layer:

- Source of truth for all records and attachments
- Enables engine migration without data loss
- Allows rebuilding engine indexes from durable storage

### Docker

```sh
# Build
docker build -t kbm ./docker
# Run (auto-creates memory if needed)
docker run -v kbm-data:/data -p 8000:8000 kbm
# If using Tailscale, use funnels to serve online
tailscale funnel --bg --set-path=/memory 8000
```

Example `docker-compose.yaml` provided in `./docker/`.

### Authentication (HTTP)

When using HTTP transport, you can secure the MCP server with GitHub OAuth.
This uses OAuth 2.0 - users authenticate via GitHub, and the server validates their identity.

1. **Create a GitHub OAuth App**:
   - Go to GitHub → Settings → Developer Settings → OAuth Apps → New OAuth App
   - Set "Authorization callback URL" to `http://your-server:8000/oauth/callback`
   - Note your Client ID and Client Secret

2. **Configure your memory**:

```yaml
# memory.yaml
transport: http
port: 8000

auth:
  provider: github
  client_id: "Ov23li..."
  client_secret: "abc123..."
  base_url: "http://localhost:8000"  # or public URL
```

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install deps
./scripts/run.sh --help  # run CLI
./scripts/test.sh        # lint, typecheck, test
```

For debugging, `$KBM_DEBUG` enables verbose logging, equivalent to `--debug` flag.

## TODO

- [ ] **CI/CD (*Quality*)**: Automated testing, linting, and deployment pipelines
  - CI:
    - Tests with coverage on push and pull requests
    - Formatting, linting and type checking on all commits
  - CD:
    - Automated releases on tags
    - Publish to PyPI
    - Build and publish Docker images to GitHub Container Registry
