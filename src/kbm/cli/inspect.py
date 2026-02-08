"""Inspect command - show what models see via MCP."""

import asyncio
from dataclasses import dataclass

from fastmcp import Client
from mcp.types import InitializeResult, Tool
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from kbm.config import MemoryConfig
from kbm.server import build_server

from . import MemoryNameArg, app, console

# MARK: Model and CMD


@dataclass
class ServerView:
    init: InitializeResult
    tools: list[Tool]

    @staticmethod
    async def introspect(config: MemoryConfig) -> "ServerView":
        mcp = build_server(config)
        async with Client(mcp) as client:
            init = client.initialize_result
            assert init is not None
            tools = await client.list_tools()
        return ServerView(init=init, tools=tools)


@app.command()
def inspect(name: str = MemoryNameArg) -> None:
    """Inspect memory MCP server."""
    cfg = MemoryConfig.from_name(name)
    view = asyncio.run(ServerView.introspect(cfg))
    _print_pretty(view)


# MARK: Pretty-Print (Claude)


def _print_pretty(view: ServerView) -> None:
    info = view.init.serverInfo
    enabled = [
        k for k, v in view.init.capabilities.model_dump().items() if v
    ]  # non-empty capabilities

    # Header from MCP initialize handshake
    header = f"[dim]FastMCP:[/dim] [dim]v{info.version}[/dim]"
    header += f"\n[dim]Protocol:[/dim] {view.init.protocolVersion}"
    if enabled:
        header += f"\n[dim]Capabilities:[/dim] {', '.join(enabled)}"

    # Instructions from the MCP initialize handshake
    if view.init.instructions:
        header += "\n[dim]Instructions:[/dim]\n" + view.init.instructions
    console.print(
        Panel(
            header,
            title=f"[bold]{info.name}[/bold]",
            title_align="left",
            border_style="",
        )
    )

    # Tools supported by the server

    if not view.tools:
        console.print("[dim]No tools registered.[/dim]")
        return

    console.print(f"[dim]Tools ({len(view.tools)}):[/dim]")
    for tool in view.tools:
        _render_tool(tool)


def _render_tool(tool: Tool) -> None:
    parts: list[object] = [tool.description or "[dim]No description[/dim]"]

    # Input schema → param table
    props: dict = (tool.inputSchema or {}).get("properties", {})
    required: list = (tool.inputSchema or {}).get("required", [])
    if props:
        tbl = Table(header_style="dim", expand=True, pad_edge=False)
        tbl.add_column("Parameter")
        tbl.add_column("Type")
        tbl.add_column("Req")
        tbl.add_column("Description")
        for pname, pschema in props.items():
            tbl.add_row(
                pname,
                _schema_type(pschema),
                "yes" if pname in required else "",
                pschema.get("description", ""),
            )
        parts += ["", tbl]

    # Annotations (non-None only)
    if tool.annotations:
        ann = tool.annotations.model_dump(exclude_none=True)
        if ann:
            parts += ["  ".join(f"[dim]{k}[/dim]={v}" for k, v in ann.items())]

    console.print(
        Panel.fit(
            _group(parts),
            title=f"[bold]{tool.name}[/bold]",
            title_align="left",
            border_style="blue",
        )
    )


def _group(parts: list[object]):
    renderables: list[RenderableType] = [
        Text.from_markup(p) if isinstance(p, str) else p  # type: ignore[misc]
        for p in parts
    ]
    return Group(*renderables)


def _schema_type(prop: dict) -> str:
    if "anyOf" in prop:
        return " | ".join(_atom(t) for t in prop["anyOf"])
    return _atom(prop)


def _atom(s: dict) -> str:
    t = s.get("type", "any")
    return f"array[{_atom(s.get('items', {}))}]" if t == "array" else str(t)
