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

| Term       | Definition                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| **Memory** | Scoped container of records (e.g., "health memory", "work memory"). Owns data and derived indexes.     |
| **Record** | Individual unit of content (text or file) within a Memory. Has ID, content, and metadata.              |
| **View**   | Read-only aggregate. Federates queries across multiple Memories. Does not own records.                 |
| **Server** | Execution boundary. Hosts exactly one Memory or View. Enforces permissions. Runs locally or remotely.  |
| **Engine** | Swappable storage implementation. A Memory uses one or more Engines (storage, vectors, graphs).        |

## Architecture

```
Client (IDE, ChatGPT, etc.)
    │
    │ connects to
    ▼
Server (auth, tools, transport)
    │
    │ hosts
    ▼
Memory (writable)                OR      View (read-only aggregate)
├── Records                              ├── Source servers list
├── Attachments                          └── Optional local index
└── Derived indexes
    │
    │ uses
    ▼
Engine(s) — storage backend
```

**Key properties:**

- Each Server is its own trust boundary
- Permissions enforced at Server level via tokens
- Views federate queries to multiple Servers
- Local use: Server via stdio (IDE, offline)
- Remote use: Server over HTTP

## Technology Stack

| Component     | Choice              | Rationale                              |
| ------------- | ------------------- | -------------------------------------- |
| Language      | Python 3.11+        | MCP SDK, ML ecosystem                  |
| MCP Framework | `mcp` SDK           | Official Anthropic SDK                 |
| RAG/Retrieval | RAG-Anything        | Multimodal, built on LightRAG          |
| Metadata DB   | SQLite              | Config, provenance, canonical copies   |
| Config        | Pydantic Settings   | Type-safe, env + files + args          |
| CLI           | Typer               | Modern, type-hint based                |
| Distribution  | pipx                | CLI install with zero friction         |

**Dev tooling:** uv (packages), ruff (lint/format), pytest (tests)

## MCP Tool Surface

### Memory Server (Writable)

| Tool          | Description                           | Required Params  |
| ------------- | ------------------------------------- | ---------------- |
| `insert`      | Add text content to the memory        | `content: str`   |
| `insert_file` | Parse & add a file (PDF, image, etc.) | `file_path: str` |
| `query`       | Retrieve relevant records             | `query: str`     |
| `delete`      | Remove a record by ID                 | `record_id: str` |
| `list`        | List all records in memory            | —                |
| `info`        | Get memory metadata                   | —                |

### View Server (Read-Only)

| Tool    | Description                             | Required Params |
| ------- | --------------------------------------- | --------------- |
| `query` | Federated search across source memories | `query: str`    |
| `list`  | List records across source memories     | —               |
| `info`  | Get view metadata                       | —               |

## Data Ownership

RAG tools handle ingestion, indexing, and retrieval. KBM ensures portability:

- If RAG tool stores in exportable format → use as source of truth
- If RAG tool uses proprietary storage → store canonical copy in SQLite

No data is ever locked in or lost due to tool changes.
