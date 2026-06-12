from __future__ import annotations

from typing import Any


def render_history_for_planning(history: list[dict[str, Any]]) -> str:
    """Render previous iterations as temporary planning context.

    TODO: This currently forwards coarse previous-round facts. Later this should
    become a smaller evaluator-owned context with dedupe and exploration hints.
    """

    if not history:
        return ""

    lines = ["", "", "历史迭代反馈（临时直传，后续替换为正式 history spec）："]
    for item in history:
        simulation_result = _as_dict(item.get("simulation_result"))
        metrics = _as_dict(simulation_result.get("metrics"))
        evaluation_report = _as_dict(item.get("evaluation_report"))
        summary_evaluation = _as_dict(item.get("summary_evaluation"))
        lines.extend(
            [
                "",
                f"## Iteration {int(item.get('iteration_index') or 0) + 1}",
                (
                    "- objective_achieved: "
                    f"{evaluation_report.get('objective_achieved', summary_evaluation.get('objective_achieved', ''))}"
                ),
                f"- target_health_delta: {metrics.get('target_health_delta', '')}",
                f"- requested_weapon_count: {metrics.get('requested_weapon_count', '')}",
                "- previous_plan:",
                str(item.get("battle_plan_md") or "").strip(),
                "- previous_summary:",
                str(item.get("summary_md") or "").strip(),
            ]
        )
    return "\n".join(lines)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
