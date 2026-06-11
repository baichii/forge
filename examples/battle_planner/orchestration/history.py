from __future__ import annotations

from typing import Any


def build_history_item(state: Any) -> dict[str, Any]:
    """Build one rough history payload from a completed iteration state.

    TODO: Replace this direct pass-through with a formal history spec after the
    feedback selection/compression rules are clear.
    """

    return {
        "iteration_index": state.iteration_index,
        "battle_plan_md": state.battle_plan_md,
        "agent_param_source": state.agent_param_source,
        "agent_param_preset_id": state.agent_param_preset_id,
        "planned_agent_params": _dump_model_list(state.planned_agent_params),
        "evaluation_report": _dump_model(state.evaluation_report),
        "evaluation_summary": _dump_model(state.evaluation_summary),
        "summary_evaluation": _dump_model(state.summary_evaluation),
        "summary_md": state.summary_md,
    }


def _dump_model(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value if isinstance(value, dict) else {}


def _dump_model_list(values: list[Any]) -> list[dict[str, Any]]:
    return [_dump_model(value) for value in values]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
