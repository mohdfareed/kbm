# Knowledge Base Manager (KBM)

> User-owned, portable knowledge layer for LLMs, exposed via the Model Context Protocol (MCP).

## Purpose

KBM solves context fragmentation across LLM tools. Instead of conversations being isolated islands, KBM provides a unified memory layer that any LLM client can access via MCP.

**Core principles:**

- User owns and controls all data
- Portable across tools, models, and time
- Backend-agnostic (storage implementations are swappable)
- Leverages existing solutions for intelligence (RAG-Anything, LightRAG)

## Terminology

| Term               | Definition                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------- |
| **Knowledge Base** | The whole system - all memories. What KBM manages.                                          |
| **Memory**         | Scoped container of records (`.kbm/` or `~/<data>/kbm/memories/<name>/`). Has config + data.|
| **Record**         | Individual unit of content (text or file) within a Memory.                                  |
| **Engine**         | Swappable storage implementation (chat-history, rag-anything).                              |

## Project Structure

```
src/kbm/              # Single package
├── __init__.py       # Public exports
├── config.py         # Settings, enums
├── engine.py         # EngineProtocol, Operation enum
├── server.py         # MCP server
├── helpers.py        # Utilities (logging, errors)
├── cli/              # CLI subpackage
│   ├── __init__.py   # Typer app, global options
│   ├── memory.py     # init, delete, list commands
│   └── server.py     # start, status, path commands
└── engines/          # Engine implementations
    ├── __init__.py   # get_engine factory
    ├── chat_history.py
    └── rag_anything.py
```

## CLI

```
kbm [-m <memory>] [-d] [-v] [-h] <command>

Options:
  -m, --memory   Memory name or path (like git -C)
  -d, --debug    Enable debug logging
  -v, --version  Show version
  -h, --help     Show help

Commands:
  init [name]    Create memory (local .kbm/ or global)
  delete <name>  Delete a global memory
  list           List all memories
  start          Start MCP server
  status         Show memory configuration
  path           Print resolved memory path
```

## Memory Layout

```
.kbm/                 # or ~/.../kbm/memories/<name>/
├── config.yaml       # Settings (engine, transport, etc.)
└── data/             # Engine-managed data
    └── <engine>/     # e.g., chat-history/, rag-anything/
```

## Technology Stack

| Component     | Choice            | Rationale                            |
| ------------- | ----------------- | ------------------------------------ |
| Language      | Python 3.12+      | MCP SDK, ML ecosystem                |
| MCP Framework | FastMCP 3         | Pythonic, cleaner API                |
| RAG/Retrieval | RAG-Anything      | Multi-modal, built on LightRAG       |
| Config        | Pydantic Settings | Type-safe, env + files               |
| CLI           | Typer             | Modern, type-hint based              |
| Distribution  | pipx              | CLI install with zero friction       |

**Dev tooling:** uv (packages), ruff (lint/format), pyright (types), pytest (tests)

## Scripts

| Script             | Purpose                                    |
| ------------------ | ------------------------------------------ |
| `scripts/run.sh`   | Run the CLI (`./scripts/run.sh <command>`) |
| `scripts/setup.sh` | Lock & sync dependencies                   |
| `scripts/check.sh` | Lint, type-check, test                     |

## MCP Tools

| Tool           | Description                   |
| -------------- | ----------------------------- |
| `query`        | Search the knowledge base     |
| `insert`       | Add text content              |
| `insert_file`  | Add a file (PDF, image, etc.) |
| `delete`       | Remove a record by ID         |
| `list_records` | List all records              |
| `info`         | Get knowledge base metadata   |

## Key Patterns

**Settings:** `Settings.use(name_or_path)` sets memory path, then `Settings()` loads config.

**Engine protocol:** `Operation` enum values match `EngineProtocol` method names. Validated at import.

**Error handling:** Raise `KBMError` for expected user errors (shown without traceback). Any other exception is a bug (full traceback shown).
