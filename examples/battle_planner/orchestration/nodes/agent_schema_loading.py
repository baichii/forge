from __future__ import annotations

from battle_planner.agents.fake_tick_agents import load_fake_tick_agent_specs
from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.runtime.trace import identity_trace


def agent_schema_loading_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("agent_schema_loading")
    state.fake_agent_specs = load_fake_tick_agent_specs()
    state.add_trace(
        identity_trace(
            "agent_schema_loading",
            "load fake tick agent schemas",
            [spec.model_dump() for spec in state.fake_agent_specs],
        )
    )
    state.cur_stage = "agent_schema_loading"
    log_node_end(
        "agent_schema_loading",
        agents=[spec.name for spec in state.fake_agent_specs],
    )
    return state
