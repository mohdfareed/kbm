# Lifetime Context System — Architecture Brief

## 1. Purpose
Build a user‑owned context system that accumulates durable memories across domains (projects, life areas, organizations) and makes them usable from multiple LLM clients (IDEs, desktop apps, mobile, ChatGPT/Claude) via MCP.

Success means:
- Context does not get stranded in a single chat/tool.
- Data remains usable for years (migrations and new retrieval tech are expected).
- Access is controllable (per domain/project, per client, sensitive vs shared).



## 2. Key Concepts

### 2.1 Store (node)
A Store is the smallest durable unit of context. It owns:
- Canonical records (text, metadata, references)
- Attachments (optional; either managed by the store or referenced)
- Derived indexes (vector/graph/etc.) that are rebuildable

A Store is addressed by a single `data_root` path/URI.

### 2.2 Graph of stores (links)
Stores are connected only in the sense that a View can include multiple Stores.

Implementation rule: treat links as implicit.
- If a Store appears in a View's `read` list, it is readable.
- If a Store appears in a View's `write` list, it is writable.

There is no separate "link" object beyond what Views declare.

### 2.3 View (access scope)
A View is the runtime selection of allowed links for a client/session.
- Chooses which readable links are active
- Chooses which writable links are active

A View is derived from configuration and authentication context.
It enforces access; it does not define new permissions.

### 2.4 MCP server (execution boundary)
The MCP server is the execution boundary that enforces access rules and exposes tools.
- One core server implementation
- Can be hosted locally (stdio) or remotely (HTTP)
- Loads one or more Stores and enforces read/write rules based on configuration and/or tokens

Transport (stdio vs HTTP) is an adapter. Core logic does not change.

### 2.5 CLI (operator UI)
CLI is the human interface to:
- Create/inspect stores
- Manage configs and views
- Run servers (stdio/HTTP)
- Admin operations (token issuance, auditing, backup/export)

## 3. System Requirements

### 3.1 Core usability
- Create a new store for a repo or life-domain in one command.
- Add and query memory from that store with low friction.
- Hard delete a store and its derived indexes.

### 3.2 Longevity
- Canonical data format must be stable and portable.
- Derived indexes must be rebuildable from canonical data.
- Backend components must be swappable (vector backend, graph backend, ingestion engine).

### 3.3 Multi-client
- Multiple local IDE workspaces can run simultaneously.
- Remote clients (mobile ChatGPT/Claude) can access via HTTP server.

### 3.4 Permissions
- Ability to restrict read/write per store.
- Ability to define curated/hardened stores (manual or controlled ingestion).
- Remote access requires authentication.

### 3.5 Canonical record constraints
- Each record has a globally unique, stable ID.
- Records include minimal provenance: created_at, source, store_id.
- Canonical records are append-only by default; edits are explicit operations.

### 3.6 Write-path rules
- Writes are allowed only to Stores listed in the active View's write set.
- Read-only Views never mutate Stores.
- Administrative writes are performed via CLI or an admin View.

### 3.7 Index lifecycle
- All indexes are derived artifacts and may be deleted and rebuilt.
- v0 freshness strategy: update on write, with full rebuild as fallback.
- Composite indexes remain deferred until a concrete performance need appears.

### 3.8 Token / View mapping
- Tokens map to named Views defined in server configuration.
- View definitions live only in config; tokens do not define permissions themselves.

### 3.9 Store identity
- Stores are referenced by a stable store_id.
- data_root may be a filesystem path or URI.
- Optional global registry may exist but is not required.

## 4. High-Level Architecture

### 4.1 Components
1) Stores (data_root)
2) Config (graph + views)
3) Server (core + transport)
4) CLI (admin + lifecycle)

### 4.2 Data placement rule
Each Store has exactly one `data_root` that may contain:
- canonical.db (or equivalent)
- attachments/
- indexes/ (vectors, graph, FTS)

No required global directory; optional global registry may exist for discovery.

## 5. Operating Modes

### 5.1 Local (IDE / trusted)
- Host launches MCP server via stdio or local HTTP.
- Server is typically scoped to a single project Store.
- Used for low-latency, offline, or sensitive data workflows.

### 5.2 Remote (shared / mobile / ChatGPT)
- A long-running HTTP MCP server exposes one or more Views.
- Clients authenticate with tokens.
- Tokens select which View is active.

Write operations may be disabled for a View. Administrative writes are performed via CLI or a separate admin View.

Local servers are not only for development; they exist to support trust boundaries, offline use, and IDE ergonomics.

## 6. Retrieval Model

### 6.1 Canonical vs derived
- Canonical: durable records + metadata + attachment refs
- Derived: per-Store indexes built from canonical data and rebuildable

### 6.2 Multi-store querying
A query executes against all Stores readable in the active View.

Baseline strategy: federated search.
- Query each Store's index independently
- Merge results in the server (ranking/limits)

Composite (cross-store) indexes are deferred unless a concrete performance need appears.

## 7. Open Decisions (to be finalized before schema)

### 7.1 Store backend
- Canonical store format (SQLite vs other)
- Per-Store derived index backend (FTS vs vector DB choice)

### 7.2 Ingestion engine
- Whether to adopt LightRAG/RAG-Anything as a pluggable ingestion/retrieval module
- Minimum ingestion requirements for v0

### 7.3 Remote auth
- Token format and issuance (PAT vs OAuth)
- How tokens map to Views (claims vs server-side mapping)

### 7.4 Canonical record contract
- Records must have stable globally-unique IDs.
- Records carry minimal provenance (created_at, source, store_id).
- Decide whether canonical records are append-only vs editable (and if editable, how history is preserved).

### 7.5 Write-path rules
- Writes are allowed only to Stores listed in the active View's `write` set.
- Read-only Views must reject all write tools.
- Admin writes are performed via CLI or a dedicated admin View.

### 7.6 Index lifecycle contract
- All indexes (FTS/vector/graph) are derived artifacts and must be rebuildable from canonical records.
- Decide the freshness model: rebuild-only vs update-on-write (with rebuild as fallback).
- Composite (cross-store) indexes remain deferred unless a concrete performance need appears.

### 7.7 Store naming and discovery
- Each Store has a stable `store_id` used across configs.
- `data_root` may be a local path or URI.
- Optional global registry is permitted for discovery but not required for correctness.

## 8. v0 Deliverable Definition
- CLI: create store, add memory, query memory, run server (stdio), inspect/delete
- MCP tools: add/get/search/list/delete (scoped to the current View)
- Config: defines primary store + optional linked stores for read-only composition
- Derived index: optional (can be FTS first; vector index may be introduced if needed)

---

Appendix: Vocabulary
- Store: durable memory unit rooted at a data_root
- View: scoped set of stores for a session
- Graph: store-link relationships
- Transport: stdio or HTTP wrapper around same server logic

