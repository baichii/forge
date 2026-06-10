from __future__ import annotations

from battle_planner.agents.scenario_understanding import understand_scenario
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.orchestration.event import (
    EventLevels,
    EventPhases,
    EventTypes,
    event_handler,
)
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.run_output_seed import load_scenario_understanding_output_seed


def scenario_understanding_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.SCENARIO_UNDERSTANDING
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={"scenario": state.scenario_name},
    )
    if settings.LLM_MODE == LLMMode.OFFLINE and settings.OUTPUT_SEED:
        seed = load_scenario_understanding_output_seed(iteration_index=state.iteration_index)
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
        output = seed.scenario_understanding_md
        trace = identity_trace(
            WorkflowStages.SCENARIO_UNDERSTANDING,
            input_value={
                "source": "run_output_seed",
                "seed_id": settings.OUTPUT_SEED,
                "scenario": state.scenario_name,
                "runtime_iteration_index": state.iteration_index,
                **seed.trace_summary,
            },
            output_value={
                "scenario_understanding_md": output,
                "trace_summary": seed.trace_summary,
            },
        )
    else:
        output, trace = understand_scenario(
            state.scenario_conf_summary,
            knowledge_pack=state.planner_knowledge_pack,
        )
    state.scenario_understanding_md = output
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
