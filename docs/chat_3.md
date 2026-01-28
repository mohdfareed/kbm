# Knowledge Base Manager (KBM) — Foundation Document

> **Purpose**: This is the implementation-ready specification for building KBM. When starting the project, this document contains all decisions, terminology, and technical details needed to begin coding.

---

## 1. Overview

**What is KBM?**
A user-owned, portable knowledge layer for LLMs, exposed via the Model Context Protocol (MCP).

**CLI:** `kbm`

**Core Principles**:
- User owns and controls all data
- Portable across tools, models, and time
- Backend-agnostic (storage implementations are swappable)
- Leverages existing solutions for intelligence (Mem0, LightRAG, etc.)

## 2. Terminology

> *Definitions of key terms used throughout the project.*

| Term               | Definition                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Knowledge Base** | The whole system — all memories. What KBM manages.                                                                                         |
| **Memory**         | Scoped container of records (e.g., "health memory", "work memory"). Owns data, attachments, and derived indexes. Writable.                 |
| **Record**         | Individual unit of content (text or file) within a Memory. Has an ID, content, and metadata.                                               |
| **View**           | Read-only aggregate. Federates queries across multiple Memories (via their Servers). May have its own derived index. Does not own records. |
| **Server**         | Execution boundary. Hosts exactly one Memory or View. Enforces permissions via tokens. Can run locally (stdio) or remotely (HTTP).         |
| **Engine**         | Swappable storage implementation. A Memory uses one or more Engines (storage, vectors, graphs).                                            |

---

## 3. Architecture

> *System layers, component responsibilities, data flow.*

### 3.1 Core Model

```
Client (IDE, ChatGPT, etc.)
    │
    │ connects to (1:1)
    ▼
Server (auth, tools, transport)
    │
    │ hosts (1:1)
    ▼
Memory (primary)             OR      View (aggregate)
├── Records                          ├── Federated query config
├── Attachments                      ├── Source servers list
└── Derived indexes                  └── Optional local index
    │                                    │
    │ uses                               │ queries
    ▼                                    ▼
Engine(s)                            Other Servers
(Sqlite, Qdrant, etc.)
```

### 3.2 Key Properties

| Property                 | How it works                        |
| ------------------------ | ----------------------------------- |
| **Trust boundary**       | Each Server is its own boundary     |
| **Permissions**          | Enforced at Server level via tokens |
| **Multi-memory queries** | View federates to multiple Servers  |
| **Local use**            | Run Server via stdio (IDE, offline) |
| **Remote use**           | Expose Server over HTTP             |

### 3.3 Memory vs View

| Aspect              | Memory | View                   |
| ------------------- | ------ | ---------------------- |
| Owns records        | Yes    | No                     |
| Writable            | Yes    | No (read-only)         |
| Has derived indexes | Yes    | Optional (local cache) |
| Federates queries   | No     | Yes                    |

## 4. Technology Stack

> *Languages, frameworks, libraries, and infrastructure choices.*

### 4.1 Core Stack

| Component     | Choice                           | Rationale                                        |
| ------------- | -------------------------------- | ------------------------------------------------ |
| Language      | **Python 3.11+**                 | MCP SDK, ML ecosystem, iteration speed           |
| MCP Framework | **`mcp` SDK**                    | Official Anthropic SDK, decorator-based          |
| RAG/Retrieval | **RAG-Anything**                 | Wrap existing tools, don't rebuild               |
| Metadata DB   | **SQLite** (via SQLAlchemy Core) | Config, provenance, canonical copies when needed |
| Config        | **Pydantic Settings**            | Type-safe, loads from env + files + args         |
| CLI           | **Typer**                        | Modern, type-hint based                          |
| Distribution  | **pipx**                         | CLI on PATH, zero friction install               |

### 4.2 Developer Tooling

| Tool           | Purpose                           |
| -------------- | --------------------------------- |
| **uv**         | Package management (fast, modern) |
| **ruff**       | Linting + formatting              |
| **pytest**     | Testing                           |
| **pre-commit** | Git hooks for quality checks      |

### 4.3 Data Ownership Principle

RAG tools (LightRAG, RAG-Anything) handle ingestion, indexing, and retrieval. However:

- If a RAG tool stores content in an **exportable, non-proprietary format** → use it as source of truth
- If a RAG tool uses **proprietary or non-exportable storage** → store a canonical copy separately in SQLite

This ensures no data is ever locked in or lost due to tool changes.

## 5. MCP Tool Surface

> *The tools exposed by the MCP server — the public API.*

### 5.1 Memory Server (Writable)

| Tool          | Description                              | Required Params  | Optional Params                |
| ------------- | ---------------------------------------- | ---------------- | ------------------------------ |
| `insert`      | Add text content to the memory           | `content: str`   | —                              |
| `insert_file` | Parse & add a file (PDF, image, etc.)    | `file_path: str` | —                              |
| `query`       | Retrieve relevant records                | `query: str`     | `mode`, `top_k`, `attachments` |
| `delete`      | Remove a record by ID                    | `record_id: str` | —                              |
| `list`        | List all records in memory               | —                | —                              |
| `info`        | Get memory metadata (record count, etc.) | —                | —                              |

### 5.2 View Server (Read-Only)

| Tool    | Description                             | Required Params | Optional Params        |
| ------- | --------------------------------------- | --------------- | ---------------------- |
| `query` | Federated search across source memories | `query: str`    | `top_k`, `attachments` |
| `list`  | List records across source memories     | —               | —                      |
| `info`  | Get view metadata                       | —               | —                      |

### 5.3 Query Parameters

| Parameter     | Type        | Default | Description                               |
| ------------- | ----------- | ------- | ----------------------------------------- |
| `top_k`       | `int`       | `10`    | Max results to return                     |
| `attachments` | `list[str]` | `[]`    | File paths (images) to include as context |

**Query modes:**
- `local` — Specific entities and immediate relationships
- `global` — High-level themes and cross-document patterns
- `hybrid` — Combines local + global (default)
- `naive` — Simple vector search, ignores graph

### 5.4 CLI-Only Operations

| Command  | Description                   |
| -------- | ----------------------------- |
| `export` | Backup/export memory data     |
| `create` | Create new memory/view config |

---

## 6. Backend Interface

> *The retrieval backend and how your system interacts with it.*

### 6.1 Backend Choice: RAG-Anything

**Why RAG-Anything:**
- Handles multimodal document parsing (PDF, DOCX, images, tables, equations)
- Built on LightRAG (graph-enhanced retrieval, multiple query modes)
- Automatic chunking, embedding, knowledge graph extraction
- Portable storage (JSON files by default)

### 6.2 Separation of Concerns

```
┌─────────────────────────────────────────────────────┐
│ KBM manages:                                        │
│  • Memory config (memory_id, data_root)             │
│  • Server config (tokens, transport)                │
│  • MCP interface                                    │
│  • Views (federation across memories)               │
└──────────────────────┬──────────────────────────────┘
                       │ configures & calls
                       ▼
┌─────────────────────────────────────────────────────┐
│ RAG-ANYTHING manages:                               │
│  • Document parsing                                 │
│  • Chunking, embedding, graph extraction            │
│  • Storage (writes to working_dir you configure)    │
│  • Query/retrieval logic                            │
└──────────────────────┬──────────────────────────────┘
                       │ writes to
                       ▼
┌─────────────────────────────────────────────────────┐
│ STORAGE (owned by RAG tool):                        │
│  working_dir/                                       │
│  ├── kv_store_full_docs.json    (original content)  │
│  ├── kv_store_text_chunks.json  (chunked text)      │
│  ├── vdb_*.json                 (vectors)           │
│  └── graph_*.graphml            (knowledge graph)   │
└─────────────────────────────────────────────────────┘
```

### 6.3 Your Role in Storage

| Responsibility         | Who      | Notes                              |
| ---------------------- | -------- | ---------------------------------- |
| Set data location      | You      | Configure `working_dir` per memory |
| Choose storage backend | You      | JSON (default) or Postgres/Qdrant  |
| Write/read data        | RAG tool | You call API, it handles storage   |
| Backup/export          | You      | Copy `working_dir` folder          |

### 6.4 Operations (Record-Level)

For v0, all operations are at the **record level**:

| Operation       | What it does                       |
| --------------- | ---------------------------------- |
| **Insert text** | Add text content to the memory     |
| **Insert file** | Parse & add PDF, DOCX, image, etc. |
| **Query**       | Retrieve relevant records          |
| **Delete**      | Remove a record by ID              |
| **List**        | List all records in memory         |
| **Export**      | Export graph/data for backup       |

Graph-level operations (delete entity, delete relation) deferred — not needed for v0.

## Appendix: Research Summary

### MCP Protocol Basics
- JSON-RPC 2.0 based, client-server architecture
- Transports: stdio (local), Streamable HTTP (remote)
- Primitives: Tools, Resources, Prompts
- Python SDK: `mcp` package

### Existing Tools Reference
- **Mem0**: Memory extraction + hybrid storage, scopes by user/agent/app/run
- **LightRAG**: Graph-enhanced RAG, excellent storage abstraction
- **Letta**: Stateful agents, memory blocks pattern
- **OpenMemory**: Local-first, Docker-based
