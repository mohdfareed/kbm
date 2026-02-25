# `kbm`

Persistent memory for LLMs, accessible via MCP.

**Usage**:

```console
$ kbm [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --version`: Show version and exit.
* `-d, --debug`: Enable debug logging.
* `-r, --root PATH`: Override home directory.
* `--help`: Show this message and exit.

**Commands**:

* `init`: Create a new memory.
* `start`: Start the MCP server.
* `inspect`: Inspect memory MCP server.
* `version`: Print application version.
* `home`: Print application home directory.
* `settings`: Print application settings.
* `memory`: Print application memory directory.

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

## `kbm version`

Print application version.

**Usage**:

```console
$ kbm version [OPTIONS]
```

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

## `kbm settings`

Print application settings.

**Usage**:

```console
$ kbm settings [OPTIONS]
```

**Options**:

* `--all TEXT`: [default: False]
* `--help`: Show this message and exit.

## `kbm memory`

Print application memory directory.

**Usage**:

```console
$ kbm memory [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: Memory name.  [default: kbm]

**Options**:

* `--all TEXT`: [default: False]
* `--help`: Show this message and exit.

