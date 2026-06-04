from __future__ import annotations

from battle_planner.orchestration.evaluation import TargetOutcomeEvaluator
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def evaluation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("evaluation", iteration_index=state.iteration_index)
    if state.simulation_result is None:
        state.mark_error("evaluation requires simulation_result")
        log_node_error(
            "evaluation",
            state.error or "missing simulation_result",
            iteration_index=state.iteration_index,
        )
        return state
    state.evaluation_report = TargetOutcomeEvaluator().evaluate(state.simulation_result)
    state.cur_stage = "evaluation"
    log_node_end(
        "evaluation",
        iteration_index=state.iteration_index,
        score=state.evaluation_report.score,
        hard_violations=len(state.evaluation_report.hard_violations),
        objective_achieved=state.evaluation_report.mission_metrics.get("objective_achieved"),
        target_health_delta=state.evaluation_report.mission_metrics.get("target_health_delta"),
        requested_weapon_count=state.evaluation_report.mission_metrics.get("requested_weapon_count"),
    )
    return state
