from __future__ import annotations

from battle_planner.agents.agent_parameter_planning import plan_agent_params
from battle_planner.config import config
from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.runtime.display_presets import select_display_agent_param_preset
from battle_planner.runtime.model_provider import build_model_provider
from battle_planner.runtime.trace import identity_trace

from forge.core.specs import TickAgentParams


def agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    if config.workflow.display_mode:
        return _display_agent_parameter_planning_node(state)

    model_provider = build_model_provider()
    log_node_start(
        "agent_parameter_planning",
        agent_count=len(state.tick_agent_specs),
        battle_plan_chars=len(state.battle_plan_md),
        display_mode=False,
        model_provider=model_provider.name,
        model=getattr(model_provider, "model", "") or model_provider.name,
    )
    planned, trace = plan_agent_params(
        scenario_understanding_md=state.scenario_understanding_md,
        battle_plan_md=state.battle_plan_md,
        agent_specs=state.tick_agent_specs,
        model=getattr(model_provider, "model", None),
        model_provider=model_provider,
    )
    state.planned_agent_params = planned
    state.agent_param_source = "llm"
    state.agent_param_preset_id = None
    state.add_trace(trace)
    state.cur_stage = "agent_parameter_planning"
    log_node_end(
        "agent_parameter_planning",
        display_mode=False,
        fallback=trace.fallback_used,
        planned_agents=_planned_agent_log_items(planned),
        error=trace.error,
    )
    return state


def _display_agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    preset = select_display_agent_param_preset(iteration_index=state.iteration_index)
    planned = [item.model_copy(deep=True) for item in preset["agents"]]
    log_node_start(
        "agent_parameter_planning",
        agent_count=len(state.tick_agent_specs),
        battle_plan_chars=len(state.battle_plan_md),
        display_mode=True,
        iteration_index=state.iteration_index,
        preset_id=preset["preset_id"],
    )
    state.planned_agent_params = planned
    state.agent_param_source = "display_preset"
    state.agent_param_preset_id = preset["preset_id"]
    state.add_trace(
        identity_trace(
            "agent_parameter_planning",
            input_value={
                "display_mode": True,
                "source": "display_preset",
                "iteration_index": state.iteration_index,
            },
            output_value={
                "source": "display_preset",
                "preset_id": preset["preset_id"],
                "description": preset.get("description", ""),
                "expected_stage": preset.get("expected_stage", ""),
                "agents": [item.model_dump(mode="json") for item in planned],
            },
        )
    )
    state.cur_stage = "agent_parameter_planning"
    log_node_end(
        "agent_parameter_planning",
        display_mode=True,
        preset_id=preset["preset_id"],
        fallback=False,
        planned_agents=_planned_agent_log_items(planned),
        error=None,
    )
    return state


def _planned_agent_log_items(planned: list[TickAgentParams]) -> list[dict]:
    return [
        {
            "agent_instance_id": item.agent_instance_id,
            "agent_name": item.agent_name,
            "agent_params": item.params,
        }
        for item in planned
    ]
