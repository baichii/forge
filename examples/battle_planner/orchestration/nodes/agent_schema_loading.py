from __future__ import annotations

from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.runtime.trace import identity_trace
from battle_planner.tick_agents.schema import load_tick_agent_specs


def agent_schema_loading_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("agent_schema_loading")
    state.tick_agent_specs = load_tick_agent_specs()
    state.add_trace(
        identity_trace(
            "agent_schema_loading",
            "load tick agent schemas",
            [spec.model_dump() for spec in state.tick_agent_specs],
        )
    )
    state.cur_stage = "agent_schema_loading"
    log_node_end(
        "agent_schema_loading",
        agents=[spec.name for spec in state.tick_agent_specs],
    )
    return state
