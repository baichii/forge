from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from battle_planner.orchestration.event import EventTypes
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.orchestration.workflow_entropy import build_graph

StreamMode = Literal["custom", "updates"]
NO_TRUNCATE_FIELDS = {"planned_agents"}


@dataclass
class WorkflowStreamResult:
    """Collected output from one streamed workflow run."""

    final_state: BattlePlannerState
    events: list[dict[str, Any]] = field(default_factory=list)
    custom_events: list[dict[str, Any]] = field(default_factory=list)
    updates: list[Any] = field(default_factory=list)


class WorkflowStreamService:
    """Outer service for streaming workflow events."""

    def __init__(self, workflow_name: str | None = None, *, graph: Any | None = None):
        self.workflow_name = workflow_name
        self.graph = graph if graph is not None else build_graph(workflow_name)

    def stream(
        self,
        initial_state: BattlePlannerState | None = None,
        *,
        print_events: bool = False,
    ) -> WorkflowStreamResult:
        state = initial_state or BattlePlannerState()
        verbose = state.verbose
        state_payload = state.model_dump(mode="json")
        events: list[dict[str, Any]] = []
        custom_events: list[dict[str, Any]] = []
        updates: list[Any] = []
        stream_modes: list[StreamMode] = ["custom", "updates"]

        for chunk in self.graph.stream(state, stream_mode=stream_modes):
            event = _normalise_stream_chunk(chunk)
            events.append(event)
            mode = event["mode"]
            payload = event["payload"]
            if mode == "custom":
                if _should_expose_event(payload, verbose):
                    custom_events.append(payload)
                if print_events and _should_print_event(payload, verbose):
                    _print_stream_event(payload)
            elif mode == "updates":
                updates.append(payload)
                _merge_update_payload(state_payload, payload)

        return WorkflowStreamResult(
            final_state=BattlePlannerState.model_validate(state_payload),
            events=events,
            custom_events=custom_events,
            updates=updates,
        )


def _normalise_stream_chunk(chunk: Any) -> dict[str, Any]:
    if isinstance(chunk, tuple) and len(chunk) == 2:
        mode, payload = chunk
        return {"mode": mode, "payload": payload}
    return {"mode": "unknown", "payload": chunk}


def _merge_update_payload(state_payload: dict[str, Any], payload: Any) -> None:
    payload = _model_dump(payload)
    if not isinstance(payload, dict):
        return

    state_fields = set(BattlePlannerState.model_fields)
    if any(key in state_fields for key in payload):
        state_payload.update(_model_dump(payload))
        return

    for value in payload.values():
        value = _model_dump(value)
        if isinstance(value, dict) and any(key in state_fields for key in value):
            state_payload.update(value)


def _model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _print_stream_event(event: Any) -> None:
    if not isinstance(event, dict):
        return
    if event.get("event_type") != EventTypes.LOG:
        return
    print(_format_log_event(event), flush=True)


def _should_expose_event(event: Any, verbose: int) -> bool:
    if not isinstance(event, dict):
        return True
    if event.get("event_type") != EventTypes.LOG:
        return True
    return _event_level(event) <= verbose


def _should_print_event(event: Any, verbose: int) -> bool:
    if not isinstance(event, dict):
        return False
    if event.get("event_type") != EventTypes.LOG:
        return False
    return _event_level(event) <= verbose


def _event_level(event: dict[str, Any]) -> int:
    level = event.get("level")
    if isinstance(level, int) and not isinstance(level, bool):
        return level
    return 1


def _format_log_event(event: dict[str, Any]) -> str:
    node = str(event.get("node") or "unknown")
    phase = str(event.get("phase") or "event")
    iteration_index = event.get("iteration_index")
    prefix = "[battle_planner]"
    if isinstance(iteration_index, int) and not isinstance(iteration_index, bool):
        prefix = f"{prefix}[{iteration_index + 1}]"

    payload = event.get("payload")
    suffix = ""
    if isinstance(payload, dict) and payload:
        suffix = " " + " ".join(f"{key}={_format_log_value(key, value)}" for key, value in payload.items())
    return f"{prefix}[{node}][{phase}]{suffix}"


def _format_log_value(key: str, value: Any) -> str:
    text = _to_log_text(value)
    if key in NO_TRUNCATE_FIELDS:
        return text
    return _shorten_text(text)


def _to_log_text(value: Any) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value).replace("\n", "\\n")


def _shorten_text(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
