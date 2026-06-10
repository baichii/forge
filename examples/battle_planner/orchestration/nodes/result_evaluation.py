from __future__ import annotations

from battle_planner.orchestration.evaluation import TargetOutcomeEvaluator
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def result_evaluation_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.RESULT_EVALUATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
    )
    if state.simulation_result is None:
        state.mark_error("evaluation requires simulation_result")
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.ERROR,
            level=EventLevels.NODE,
            iteration_index=state.iteration_index,
            payload={"error": state.error or "missing simulation_result"},
        )
        return state
    state.evaluation_report = TargetOutcomeEvaluator().evaluate(state.simulation_result)
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "score": state.evaluation_report.score,
            "hard_violations": len(state.evaluation_report.hard_violations),
            "objective_achieved": state.evaluation_report.mission_metrics.get("objective_achieved"),
            "target_health_delta": state.evaluation_report.mission_metrics.get("target_health_delta"),
            "requested_weapon_count": state.evaluation_report.mission_metrics.get("requested_weapon_count"),
        },
    )
    return state
