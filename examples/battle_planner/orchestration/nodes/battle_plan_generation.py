from __future__ import annotations

from battle_planner.agents.battle_plan_generation import generate_battle_plan
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.run_output_seed import load_battle_plan_generation_output_seed


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
    if settings.LLM_MODE == LLMMode.OFFLINE and settings.OUTPUT_SEED:
        seed = load_battle_plan_generation_output_seed(iteration_index=state.iteration_index)
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.MESSAGE,
            level=EventLevels.DETAIL,
            iteration_index=state.iteration_index,
            payload={
                "source": "run_output_seed",
                "seed_id": settings.OUTPUT_SEED,
                "runtime_iteration_index": state.iteration_index,
                **seed.trace_summary,
            },
        )
        output = seed.battle_plan_md
        trace = identity_trace(
            WorkflowStages.BATTLE_PLAN_GENERATION,
            input_value={
                "source": "run_output_seed",
                "seed_id": settings.OUTPUT_SEED,
                "runtime_iteration_index": state.iteration_index,
                "history_items": len(state.history),
                **seed.trace_summary,
            },
            output_value={
                "battle_plan_md": output,
                "trace_summary": seed.trace_summary,
            },
        )
    else:
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
