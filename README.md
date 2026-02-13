# KBM - Knowledge Base Manager

[![CI](https://github.com/mohdfareed/kbm/actions/workflows/ci.yaml/badge.svg)](https://github.com/mohdfareed/kbm/actions/workflows/ci.yaml)
![Coverage](https://img.shields.io/badge/coverage-6.62s%25-red)
[![Version](https://img.shields.io/github/v/tag/mohdfareed/kbm?label=version)](https://github.com/mohdfareed/kbm/releases)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://github.com/mohdfareed/kbm)
[![License](https://img.shields.io/github/license/mohdfareed/kbm)](LICENSE)

Persistent memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Install

```sh
uv tool install git+https://github.com/mohdfareed/kbm
pipx install git+https://github.com/mohdfareed/kbm
```

## Quick Start

```sh
kbm start # defaults to cwd name
kbm start notes
```

## Configuration

* Environment variables (`KBM_*`) override config. Loaded from `.env`, `.kbm.env`, or shell.
* Data lives at `$KBM_HOME` (default: platform data dir).
  * Backup/migrate by copying this directory.
* `kbm status <name> --full` shows all config options with defaults.

## Features

**Engines** provide different retrieval strategies:

- `chat-history` - SQLite database with FTS5 search
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

**Create a GitHub OAuth App**:
   - Go to GitHub → Settings → Developer Settings → OAuth Apps → New OAuth App
   - Set "Authorization callback URL" to `http://your-server:8000/oauth/callback`
   - Add the Client ID and Client Secret to the memory configuration

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/run.sh -h  # run CLI through `uv`
./scripts/run.sh -i  # install dev version locally
./scripts/test.sh    # must be used before committing
```

## TODO

- [ ] **Templates**: Support using a pre-existing memory config file for `init` calls.
  - Look for a config file at `$KBM_HOME` to use for creating new memories.
  - The file is manually edited by the user to override certain defaults.
  - The path is shown using the command `kbm -S`, with other app settings.
- [ ] **Authorization**: Implement role-based access control (RBAC) for HTTP transport.
  - Define permissions per tool.
  - Add config to define role-permission and user-role mappings.
  - Define users using tokens based on the authentication provider.
    - For example, email addresses/domain-wildcards for GitHub OAuth users.
    - For local auth, generate random tokens mapped to roles and provided to clients then sent back with requests (research if possible).
  - Implement middleware to check permissions on each request.
- [ ] **Re-indexing Command**: CLI command to rebuild engine indexes from canonical storage.
  - `kbm reindex <memory_name>`: Rebuilds the engine index for the specified memory using records from canonical storage.
  - Migration supported by changing engine type and re-indexing.
- [ ] **GitHub Models Provider**: Add `Provider.GITHUB` convenience for rag-anything.
  - OpenAI-compatible API at `https://models.github.ai/inference` — LLM + embeddings.
  - Auth: GitHub PAT. Useful where only GitHub/Copilot access is available (IT policy).
  - Default models: `gpt-4o-mini`, `text-embedding-3-small` (1536 dims).
  - Implemented as preset on existing OpenAI provider (set `base_url` + defaults).
- [ ] **MCP Sampling for LLM**: Use `ctx.sample()` for rag-anything LLM calls.
  - Server borrows the client's LLM instead of direct API calls.
  - Thread FastMCP `Context` into engine pipeline (store on instance per tool call).
  - Sampling only covers text generation; embeddings still need a provider (GitHub, OpenAI, etc.).
  - Fallback to configured provider for clients that don't support sampling.
- [ ] **Documentation**: Add examples and templates to `docs/`.
  - Add config file examples with authentication, GitHub-provided LLMs, etc.
  - Add example docker compose files.
- [ ] **Display Config Options**: In `kbm status`, show possible enum values.
