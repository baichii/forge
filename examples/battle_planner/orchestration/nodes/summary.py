from __future__ import annotations

from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.planning.summary_generation import generate_summary


def summary_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "summary",
        simulation_ready=state.simulation_result is not None,
        evaluation_ready=state.evaluation_report is not None,
    )
    if state.simulation_result is None or state.evaluation_report is None:
        state.mark_error("summary requires simulation_result and evaluation_report")
        log_node_error("summary", state.error or "missing inputs")
        return state
    output, trace = generate_summary(
        scenario_understanding_md=state.scenario_understanding_md,
        battle_plan_md=state.battle_plan_md,
        planned_agent_params=state.planned_agent_params,
        simulation_result=state.simulation_result,
        evaluation_report=state.evaluation_report,
    )
    state.summary_md = output
    state.add_trace(trace)
    state.cur_stage = "complete"
    log_node_end(
        "summary",
        fallback=trace.fallback_used,
        output_chars=len(output),
        error=trace.error,
    )
    return state
