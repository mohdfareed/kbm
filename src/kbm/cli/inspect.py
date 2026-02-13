"""Inspect command - show what models see via MCP."""

import asyncio
from dataclasses import dataclass

from fastmcp import Client
from mcp.types import InitializeResult, Tool
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from kbm.config import MemoryConfig
from kbm.mcp.server import build_server

from . import MemoryNameArg, app, console

# MARK: Model and CMD


@dataclass
class ServerView:
    init: InitializeResult
    tools: list[Tool]

    @staticmethod
    async def introspect(memory: MemoryConfig) -> "ServerView":
        mcp = build_server(memory)
        async with Client(mcp) as client:
            init = client.initialize_result
            assert init is not None
            tools = await client.list_tools()
        return ServerView(init=init, tools=tools)


@app.command()
def inspect(name: str = MemoryNameArg) -> None:
    """Inspect memory MCP server."""
    memory = MemoryConfig.from_name(name)
    view = asyncio.run(ServerView.introspect(memory))
    _print_pretty(view)


# MARK: Pretty-Print (Claude)


def _print_pretty(view: ServerView) -> None:
    info = view.init.serverInfo
    enabled = [
        k for k, v in view.init.capabilities.model_dump().items() if v
    ]  # non-empty capabilities

    # Header from MCP initialize handshake

    header = f"[dim]FastMCP:[/] [dim]v{info.version}[/]"
    header += f"\n[dim]Protocol:[/] {view.init.protocolVersion}"
    if enabled:
        header += f"\n[dim]Capabilities:[/] {', '.join(enabled)}"

    console.print(
        Panel(
            header,
            title=f"[bold]{info.name}[/]",
            title_align="left",
            border_style="dim",
        )
    )

    # Interface panel containing instructions and tools

    interface_parts: list[RenderableType] = []

    if view.init.instructions:
        interface_parts.append(Panel(view.init.instructions, border_style="dim"))
    if not view.tools:
        interface_parts.append(Text("[dim]No tools registered.[/]"))
    else:
        interface_parts.append(Rule(f"Tools ({len(view.tools)})", style="bold"))

        for tool in view.tools:
            interface_parts.append(_render_tool_panel(tool))

    console.print(
        Panel(
            Group(*interface_parts),
            title=f"[bold]Instructions[/]",
            title_align="left",
            border_style="",
        )
    )


def _render_tool_panel(tool: Tool) -> Panel:
    parts: list[object] = [tool.description or "[dim]No description[/]"]

    # Input schema → param table
    props: dict = (tool.inputSchema or {}).get("properties", {})
    required: list = (tool.inputSchema or {}).get("required", [])
    if props:
        tbl = Table(header_style="dim", expand=True, pad_edge=False)
        tbl.add_column("Parameter")
        tbl.add_column("Type")
        tbl.add_column("Req.")
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
            parts += ["  ".join(f"[dim]{k}[/]={v}" for k, v in ann.items())]

    return Panel.fit(
        _group(parts),
        title=f"[bold]{tool.name}[/]",
        title_align="left",
        border_style="blue",
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
