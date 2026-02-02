# KBM - Knowledge Base Manager

Persistent memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

KBM gives any MCP-compatible client (IDEs, ChatGPT, Claude, etc.) access to a shared knowledge base. Context accumulates across conversations, tools, and time - so every model you talk to can pick up where the last one left off.

## Requirements

- Python 3.12+
- `pipx` (recommended) or `pip`
- `uv` (development)

## Install

```sh
pipx install git+https://github.com/mohdfareed/kbm
kbm -h
```

## Quick Start

```sh
kbm init               # create default config file
kbm start stdio        # start MCP server (stdio transport)
kbm memory query "x"   # search the knowledge base
kbm memory insert "y"  # add content
```

## MCP Tools

| Tool           | Description                   |
| -------------- | ----------------------------- |
| `query`        | Search the knowledge base     |
| `insert`       | Add text content              |
| `insert_file`  | Add a file (PDF, image, etc.) |
| `delete`       | Remove a record by ID         |
| `list_records` | List all records              |
| `info`         | Get knowledge base metadata   |

## Configuration

Settings load from a config file (`.env`, `.kbm.json`, or `.kbm/config.json`) with env var overrides. Supports ENV, JSON, and YAML formats. The file is discovered automatically, or can be specified with `--config`.

```sh
kbm init --format json  # create default .kbm.json
kbm config              # show current config
```

**Key settings:**

| Setting                       | Env Var                             | Description                                      |
| ----------------------------- | ----------------------------------- | ------------------------------------------------ |
| `engine`                      | `KBM_ENGINE`                        | Storage backend (`rag-anything`, `chat-history`) |
| `server_name`                 | `KBM_SERVER_NAME`                   | MCP server name                                  |
| `data_dir`                    | `KBM_DATA_DIR`                      | Data storage location                            |
| `prompts.server_instructions` | `KBM__PROMPTS__SERVER_INSTRUCTIONS` | Custom instructions for LLMs                     |

## Development

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install dependencies
./scripts/run.sh --help  # run CLI
./scripts/check.sh       # lint, type-check, test
```

## TODO

- [ ] **Canonical data and metadata (*Portability*)**: Store all records and attachments with metadata to allow import/export and engine migration
  - Uses SQLite or similar for structured storage
  - Metadata: source, timestamp, tags, original engine ,etc.
  - Import/export commands (JSONL, CSV, raw, etc.)
- [ ] **Federation engine (*Scalability*)**: Aggregate multiple memories; support direct config paths (instantiate engine) or server URLs (MCP client); and route requests based on capabilities
  - Implements `EngineProtocol`
  - Routes requests to sub-engines based on capabilities
  - Aggregation strategies (e.g. merge results, round-robin, priority-based)
  - Allows writing by allowing model to specify target knowledge base

**Future Enhancements:**

- [ ] **Authorization (*Security*)**: Add API key support for HTTP server mode
  - API key generation and management commands
  - Key validation middleware for MCP requests and CLI/web access
  - Read/write scopes
- [ ] **Web interface (*Usability*)**: Simple web UI for browsing and managing the knowledge base
  - Manage app settings, including engine selection
  - Browse, search, and manage records
  - View usage stats and logs
- [ ] **CI/CD (*Quality*)**: Automated testing, linting, and deployment pipelines
  - CI:
    - Tests on push and pull requests
    - Linting and type checking
  - CD:
    - Automated releases on tags
    - Publish to PyPI

## License

[MIT](LICENSE)
