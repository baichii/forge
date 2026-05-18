from __future__ import annotations

from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.planning.battle_plan_generation import generate_battle_plan


def battle_plan_generation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "battle_plan_generation",
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
        fallback=trace.fallback_used,
        output_chars=len(output),
        error=trace.error,
    )
    return state
