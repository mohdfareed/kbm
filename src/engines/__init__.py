"""Storage engines."""

__all__ = ["create_engine_app", "get_engine", "register_engine"]

from typing import TYPE_CHECKING, Callable

import typer

from app.config import get_settings
from app.engine import CAPABILITY_METHODS, REQUIRED_METHODS, EngineProtocol
from app.helpers import get_docstring, make_sync_command
from engines import get_engine

if TYPE_CHECKING:
    from app.engine import EngineProtocol

# Registry is module-level by necessity - decorators populate it at class definition
_registry: dict[str, type["EngineProtocol"]] = {}


def register_engine(name: str):
    """Decorator to register an engine class."""

    def decorator[T](cls: type[T]) -> type[T]:
        _registry[name] = cls  # type: ignore[assignment]
        return cls

    return decorator


def get_engine(name: str) -> "EngineProtocol":
    """Get an engine instance by name."""
    # Lazy import to trigger @register_engine decorators
    import engines.chat_history
    import engines.rag_anything

    if name not in _registry:
        available = ", ".join(_registry.keys()) or "(none)"
        raise KeyError(f"Unknown engine: {name}. Available: {available}")
    return _registry[name]()


def create_engine_app() -> typer.Typer:
    """Create memory app with commands based on engine capabilities.

    Typer introspects function signatures automatically - commands are
    created by copying method signatures via make_sync_command().
    """
    app = typer.Typer(name="memory", help="Knowledge base memory operations.")

    settings = get_settings()
    engine = get_engine(settings.engine.value)
    engine_cls = type(engine)
    caps = engine.capabilities

    def _get_engine() -> EngineProtocol:
        return get_engine(get_settings().engine.value)

    def _register(method: Callable) -> None:
        name = method.__name__
        cli_name = name.replace("_", "-")
        cmd = make_sync_command(getattr(engine_cls, name), _get_engine)
        app.command(name=cli_name, help=get_docstring(method))(cmd)

    for method in REQUIRED_METHODS:
        _register(method)

    for cap, method in CAPABILITY_METHODS.items():
        if cap in caps:
            _register(method)

    for extra_tool in engine.get_extra_tools():
        _register(extra_tool)

    return app
