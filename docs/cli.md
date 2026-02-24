# `kbm`

Persistent memory for LLMs, accessible via MCP.

**Usage**:

```console
$ kbm [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-d, --debug`: Enable debug logging.
* `-r, --root PATH`: Override home directory.
* `-s, --settings`: Show app settings overrides and exit.
* `-S, --all-settings`: Show all app settings and exit.
* `-v, --version`: Show version and exit.
* `--help`: Show this message and exit.

**Commands**:

* `init`: Create a new memory.
* `start`: Start the MCP server.
* `list`: List all memories.
* `status`: Show memory configuration.
* `delete`: Permanently delete a memory and all its data.
* `inspect`: Inspect memory MCP server.
* `home`: Print application home directory.

## `kbm init`

Create a new memory.

**Usage**:

```console
$ kbm init [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `-e, --engine [chat-history|markdown|rag-anything|mem0]`: [default: chat-history]
* `-f, --force`: Overwrite if exists.
* `--help`: Show this message and exit.

## `kbm start`

Start the MCP server.

**Usage**:

```console
$ kbm start [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `-e, --engine [chat-history|markdown|rag-anything|mem0]`: Memory engine.
* `-t, --transport [stdio|http]`
* `-H, --host TEXT`
* `-p, --port INTEGER`
* `--path TEXT`: URL path/subpath for HTTP.
* `--help`: Show this message and exit.

## `kbm list`

List all memories.

**Usage**:

```console
$ kbm list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `kbm status`

Show memory configuration.

**Usage**:

```console
$ kbm status [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `-f, --full`: Show all options with defaults.
* `-p, --path`: Show config file path.
* `--help`: Show this message and exit.

## `kbm delete`

Permanently delete a memory and all its data.

**Usage**:

```console
$ kbm delete [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `-y, --yes`: Skip confirmation.
* `--help`: Show this message and exit.

## `kbm inspect`

Inspect memory MCP server.

**Usage**:

```console
$ kbm inspect [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `--help`: Show this message and exit.

## `kbm home`

Print application home directory.

**Usage**:

```console
$ kbm home [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

