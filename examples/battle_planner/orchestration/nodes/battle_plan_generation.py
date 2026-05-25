from __future__ import annotations

from battle_planner.agents.battle_plan_generation import generate_battle_plan
from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def battle_plan_generation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "battle_plan_generation",
        iteration_index=state.iteration_index,
        scenario_md_chars=len(state.scenario_understanding_md),
    )
    output, trace = generate_battle_plan(
        state.scenario_understanding_md,
        knowledge_pack=state.planner_knowledge_pack,
    )
    state.battle_plan_md = output
    state.add_trace(trace)
    state.cur_stage = "battle_plan_generation"
    log_node_end(
        "battle_plan_generation",
        iteration_index=state.iteration_index,
        fallback=trace.fallback_used,
        output_chars=len(output),
        error=trace.error,
    )
    return state
