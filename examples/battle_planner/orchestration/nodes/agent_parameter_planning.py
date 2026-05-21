from __future__ import annotations

from battle_planner.agents.agent_parameter_planning import plan_agent_params
from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "agent_parameter_planning",
        agent_count=len(state.tick_agent_specs),
        battle_plan_chars=len(state.battle_plan_md),
    )
    planned, trace = plan_agent_params(
        scenario_understanding_md=state.scenario_understanding_md,
        battle_plan_md=state.battle_plan_md,
        agent_specs=state.tick_agent_specs,
    )
    state.planned_agent_params = planned
    state.add_trace(trace)
    state.cur_stage = "agent_parameter_planning"
    log_node_end(
        "agent_parameter_planning",
        fallback=trace.fallback_used,
        planned_agents=[
            {
                "agent_instance_id": item.agent_instance_id,
                "agent_name": item.agent_name,
            }
            for item in planned
        ],
        error=trace.error,
    )
    return state
