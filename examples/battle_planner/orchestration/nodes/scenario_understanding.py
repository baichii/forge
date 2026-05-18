from __future__ import annotations

from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.planning.scenario_understanding import understand_scenario


def scenario_understanding_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("scenario_understanding", scenario=state.scenario_name)
    output, trace = understand_scenario(state.scenario_conf_summary)
    state.scenario_understanding_md = output
    state.add_trace(trace)
    state.cur_stage = "scenario_understanding"
    log_node_end(
        "scenario_understanding",
        fallback=trace.fallback_used,
        output_chars=len(output),
        error=trace.error,
    )
    return state
