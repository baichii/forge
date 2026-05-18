from __future__ import annotations

from battle_planner.evaluation.evaluator import RandomDemoEvaluator
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def evaluation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("evaluation")
    if state.simulation_result is None:
        state.mark_error("evaluation requires simulation_result")
        log_node_error("evaluation", state.error or "missing simulation_result")
        return state
    state.evaluation_report = RandomDemoEvaluator().evaluate(state.simulation_result)
    state.cur_stage = "evaluation"
    log_node_end(
        "evaluation",
        score=state.evaluation_report.score,
        hard_violations=len(state.evaluation_report.hard_violations),
    )
    return state
