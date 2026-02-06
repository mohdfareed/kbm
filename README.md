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

* Environment variables (`KBM_*`) override config. Loaded from `.kbm.env`, `.env`, or shell.
* Data lives at `$KBM_HOME/data/<name>/` (default: platform data dir).
  * `kbm home` displays the data directory.
  * Backup by copying this directory.
`kbm init` creates a new memory with a default config with all possible options.
`kbm status` shows the current configuration of a memory.

## Features

**Engines** provide different retrieval strategies:

- `chat-history` - Simple JSON storage for conversations
- `rag-anything` - Multi-modal RAG with LightRAG
- `federation` - Aggregates queries across multiple memories, local and remote

**Canonical Storage** wraps all writable engines with a SQLite-backed persistence layer:

- Source of truth for all records and attachments
- Enables engine migration without data loss
- Allows rebuilding engine indexes from durable storage

**Federation** enables querying multiple knowledge bases as one:

- Aggregates results from local memories and remote MCP servers
- Configures sources via:
  - `federation.memories` - names of local/global memories,
  - `federation.configs` - paths to config files, and
  - `federation.remotes` - MCP server URLs
- Read-only: can only query remote memories

### Docker

```sh
# Build
docker build -t kbm ./docker
# Run (auto-creates memory if needed)
docker run -v kbm-data:/data -p 8000:8000 kbm
```

Example `docker-compose.yaml` provided in `./docker/`.

### Authentication (HTTP)

When using HTTP transport, you can secure your server with GitHub OAuth. This uses OAuth 2.0 - users authenticate via GitHub, and the server validates their identity.

#### Setup

1. **Create a GitHub OAuth App**:
   - Go to GitHub → Settings → Developer Settings → OAuth Apps → New OAuth App
   - Set "Authorization callback URL" to `http://your-server:8000/oauth/callback`
   - Note your Client ID and Client Secret

2. **Configure your memory**:

```yaml
# .kbm.yaml
transport: http
port: 8000

auth:
  provider: github
  client_id: "Ov23li..."
  client_secret: "abc123..."
  base_url: "http://localhost:8000"  # or public URL
  allowed_emails: # empty = allow all
    - alice@company.com
    - bob@company.com
  read_only_emails:
    - intern@company.com  # can query but not insert/delete
```

#### How it works

1. Client connects to your MCP server over HTTP
2. Server redirects to GitHub login (opens browser)
3. User authorizes and GitHub returns a token
4. Server validates the token and checks email against allowlist
5. Read-only users can only use `query` and `info` tools

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install deps
./scripts/run.sh --help  # run CLI
./scripts/check.sh       # lint, typecheck, test
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
