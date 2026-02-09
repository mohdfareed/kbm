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
| `scripts/test.sh`  | Lint, type-check, test                     |
