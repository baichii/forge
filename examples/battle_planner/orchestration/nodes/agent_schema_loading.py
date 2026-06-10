from __future__ import annotations

from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.resource.loader import load_tick_agent_specs


def agent_schema_loading_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.AGENT_SCHEMA_LOADING
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
    )
    state.tick_agent_specs = load_tick_agent_specs()
    state.add_trace(
        identity_trace(
            WorkflowStages.AGENT_SCHEMA_LOADING,
            "load tick agent schemas",
            [spec.model_dump() for spec in state.tick_agent_specs],
        )
    )
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={"agents": [spec.name for spec in state.tick_agent_specs]},
    )
    return state
