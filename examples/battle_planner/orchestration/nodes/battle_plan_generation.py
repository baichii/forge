from __future__ import annotations

from battle_planner.agents.battle_plan_generation import generate_battle_plan
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def battle_plan_generation_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.BATTLE_PLAN_GENERATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "scenario_md_chars": len(state.scenario_understanding_md),
            "history_items": len(state.history),
        },
    )
    output, trace = generate_battle_plan(
        state.scenario_understanding_md,
        knowledge_pack=state.planner_knowledge_pack,
        history=state.history,
    )
    state.battle_plan_md = output
    state.add_trace(trace)
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "fallback": trace.fallback_used,
            "output_chars": len(output),
            "error": trace.error,
        },
    )
    return state
