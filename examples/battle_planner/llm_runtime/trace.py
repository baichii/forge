from __future__ import annotations

from typing import Any

from battle_planner.model import LLMTrace


def build_trace(
    *,
    node_name: str,
    input_messages: list[dict[str, Any]],
    raw_output: str,
    parsed_output: Any | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    fallback_used: bool = False,
    error: str | None = None,
) -> LLMTrace:
    return LLMTrace(
        node_name=node_name,
        input_messages=input_messages,
        raw_output=raw_output,
        parsed_output=parsed_output,
        tool_calls=tool_calls or [],
        fallback_used=fallback_used,
        error=error,
    )


def identity_trace(node_name: str, input_value: Any, output_value: Any) -> LLMTrace:
    return build_trace(
        node_name=node_name,
        input_messages=[{"role": "system", "content": "identity placeholder"}],
        raw_output=str(output_value),
        parsed_output=output_value,
        fallback_used=False,
        error=None,
    )
