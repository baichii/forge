from __future__ import annotations

from battle_planner.orchestration.evaluation import (
    TargetOutcomeEvaluator,
    aggregate_evaluation_reports,
)
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
    simulation_results = list(state.simulation_results)
    if not simulation_results and state.simulation_result is not None:
        simulation_results = [state.simulation_result]
    if not simulation_results:
        state.mark_error("evaluation requires simulation_results")
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.ERROR,
            level=EventLevels.NODE,
            iteration_index=state.iteration_index,
            payload={"error": state.error or "missing simulation_results"},
        )
        return state
    evaluator = TargetOutcomeEvaluator()
    evaluation_reports = [evaluator.evaluate(result) for result in simulation_results]
    state.evaluation_reports = evaluation_reports
    state.evaluation_report = evaluation_reports[0] if evaluation_reports else None
    state.evaluation_summary = aggregate_evaluation_reports(evaluation_reports, simulation_results)
    state.cur_stage = node_name
    first_metrics = simulation_results[0].metrics if simulation_results else {}
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "run_count": len(state.evaluation_reports),
            "mean_score": state.evaluation_summary.mean_score if state.evaluation_summary else None,
            "success_rate": state.evaluation_summary.success_rate if state.evaluation_summary else None,
            "findings": len(state.evaluation_report.findings) if state.evaluation_report else None,
            "objective_achieved": state.evaluation_report.objective_achieved
            if state.evaluation_report
            else None,
            "target_health_delta": first_metrics.get("target_health_delta"),
            "requested_weapon_count": first_metrics.get("requested_weapon_count"),
        },
    )
    return state
