from __future__ import annotations

from battle_planner.agents.agent_parameter_planning import plan_agent_params
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.model_provider import build_model_provider
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.run_output_seed import load_agent_parameter_planning_output_seed

from forge.core.specs import TickAgentParams


def agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    if settings.LLM_MODE == LLMMode.OFFLINE:
        return _run_output_seed_agent_parameter_planning_node(state)

    model_provider = build_model_provider()
    node_name = WorkflowStages.AGENT_PARAMETER_PLANNING
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "agent_count": len(state.tick_agent_specs),
            "battle_plan_chars": len(state.battle_plan_md),
            "display_mode": False,
            "model_provider": model_provider.name,
            "model": getattr(model_provider, "model", "") or model_provider.name,
        },
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
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "display_mode": False,
            "fallback": trace.fallback_used,
            "planned_agents": _planned_agent_log_items(planned),
            "error": trace.error,
        },
    )
    return state


def _run_output_seed_agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    seed = load_agent_parameter_planning_output_seed(iteration_index=state.iteration_index)
    planned = [item.model_copy(deep=True) for item in seed.planned_agent_params]
    node_name = WorkflowStages.AGENT_PARAMETER_PLANNING
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "agent_count": len(state.tick_agent_specs),
            "battle_plan_chars": len(state.battle_plan_md),
            "source": "run_output_seed",
            "preset_id": seed.preset_id,
        },
    )
    state.planned_agent_params = planned
    state.agent_param_source = "run_output_seed"
    state.agent_param_preset_id = seed.preset_id
    state.add_trace(
        identity_trace(
            WorkflowStages.AGENT_PARAMETER_PLANNING,
            input_value={
                "source": "run_output_seed",
                "seed_id": settings.OUTPUT_SEED,
                "runtime_iteration_index": state.iteration_index,
                **seed.trace_summary,
            },
            output_value={
                "source": "run_output_seed",
                "preset_id": seed.preset_id,
                "trace_summary": seed.trace_summary,
                "agents": [item.model_dump(mode="json") for item in planned],
            },
        )
    )
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "source": "run_output_seed",
            "preset_id": seed.preset_id,
            "fallback": False,
            "planned_agents": _planned_agent_log_items(planned),
            "error": None,
        },
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
