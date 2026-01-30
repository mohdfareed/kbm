# KBM — Knowledge Base Manager

Persistent memory for LLMs via the [Model Context Protocol](https://modelcontextprotocol.io/).

KBM gives any MCP-compatible client (IDEs, ChatGPT, Claude, etc.) access to a shared knowledge base. Context accumulates across conversations, tools, and time — so every model you talk to can pick up where the last one left off.

## Install

```sh
pipx install git+https://github.com/mohdfareed/kbm
```

## Quick Start

```sh
kbm init               # create default config file
kbm start              # start MCP server (stdio)
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

Settings load from a config file (`.env`, `kbm.yaml`, or `kbm.json`) with env var overrides.

```sh
kbm init --format env          # create .env instead
kbm config                     # show current config
```

**Key settings:**

| Setting                       | Env Var                             | Description                                      |
| ----------------------------- | ----------------------------------- | ------------------------------------------------ |
| `engine`                      | `KBM_ENGINE`                        | Storage backend (`rag-anything`, `chat-history`) |
| `server_name`                 | `KBM_SERVER_NAME`                   | MCP server name                                  |
| `data_dir`                    | `KBM_DATA_DIR`                      | Data storage location                            |
| `prompts.server_instructions` | `KBM__PROMPTS__SERVER_INSTRUCTIONS` | Custom instructions for LLMs                     |

## Development

Requires [`uv`](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/mohdfareed/kbm && cd kbm
./scripts/setup.sh       # install dependencies
./scripts/run.sh --help  # run CLI
./scripts/check.sh       # lint, type-check, test
```

## License

[MIT](LICENSE)
