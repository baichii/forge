from __future__ import annotations

import json
from typing import Any

NO_TRUNCATE_FIELDS = {"planned_agents"}


def log_node_start(node_name: str, **fields: Any) -> None:
    print(_format_line(node_name, "start", fields), flush=True)


def log_node_end(node_name: str, **fields: Any) -> None:
    print(_format_line(node_name, "end", fields), flush=True)


def log_node_error(node_name: str, error: str) -> None:
    print(_format_line(node_name, "error", {"error": error}), flush=True)


def _format_line(node_name: str, event: str, fields: dict[str, Any]) -> str:
    suffix = ""
    if fields:
        suffix = " " + " ".join(f"{key}={_format_value(key, value)}" for key, value in fields.items())
    return f"[battle_planner][{node_name}][{event}]{suffix}"


def _format_value(key: str, value: Any) -> str:
    text = _to_log_text(value)
    if key in NO_TRUNCATE_FIELDS:
        return text
    return _shorten_text(text)


def _to_log_text(value: Any) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value).replace("\n", "\\n")


def _shorten(value: Any, limit: int = 160) -> str:
    return _shorten_text(str(value).replace("\n", "\\n"), limit=limit)


def _shorten_text(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
