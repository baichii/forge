from __future__ import annotations

from typing import Any


def log_node_start(node_name: str, **fields: Any) -> None:
    print(_format_line(node_name, "start", fields), flush=True)


def log_node_end(node_name: str, **fields: Any) -> None:
    print(_format_line(node_name, "end", fields), flush=True)


def log_node_error(node_name: str, error: str) -> None:
    print(_format_line(node_name, "error", {"error": error}), flush=True)


def _format_line(node_name: str, event: str, fields: dict[str, Any]) -> str:
    suffix = ""
    if fields:
        suffix = " " + " ".join(f"{key}={_shorten(value)}" for key, value in fields.items())
    return f"[battle_planner][{node_name}][{event}]{suffix}"


def _shorten(value: Any, limit: int = 160) -> str:
    text = str(value).replace("\n", "\\n")
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
