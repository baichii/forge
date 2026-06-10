from __future__ import annotations

from contextlib import suppress
from typing import Any, Callable, Literal

EventType = Literal["log", "event"]
EventPhase = Literal["start", "end", "error", "message"]
EventLevel = Literal[1, 2]


class EventTypes:
    """工作流事件类型常量。"""

    LOG = "log"
    EVENT = "event"


class EventPhases:
    """节点事件阶段常量。"""

    START = "start"
    END = "end"
    ERROR = "error"
    MESSAGE = "message"


class EventLevels:
    """事件捕获等级常量。"""

    NODE = 1
    DETAIL = 2


def event_handler(
    event_type: EventType,
    *,
    node: str,
    phase: EventPhase,
    level: EventLevel,
    payload: dict[str, Any] | None = None,
    iteration_index: int | None = None,
) -> None:
    """在可用的 LangGraph stream 中捕获结构化事件。

    Args:
        event_type: 事件类型，`log` 用于观察记录，`event` 预留给流程事件。
        node: 发出事件的节点名。
        phase: 当前节点阶段。
        level: 事件等级，用于外层按需过滤。
        payload: 结构化载荷。
        iteration_index: 可选的迭代序号。
    """

    writer = _get_stream_writer()
    if writer is None:
        return
    writer(
        {
            "event_type": event_type,
            "node": node,
            "phase": phase,
            "level": level,
            "iteration_index": iteration_index,
            "payload": _to_event_value(payload or {}),
        }
    )


def _get_stream_writer() -> Callable[[dict[str, Any]], None] | None:
    with suppress(Exception):
        from langgraph.config import get_stream_writer

        return get_stream_writer()
    return None


def _to_event_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _to_event_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_event_value(item) for item in value]
    if isinstance(value, tuple):
        return [_to_event_value(item) for item in value]
    return value
