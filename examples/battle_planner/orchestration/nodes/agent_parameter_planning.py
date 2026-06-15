from __future__ import annotations

from battle_planner.agents.agent_parameter_planning import plan_branch_executions
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.model_provider import build_model_provider
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.model import SchemeBranchExecutionSpec
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
    branch_executions, trace = plan_branch_executions(
        scenario_understanding_md=state.scenario_understanding_md,
        battle_plan_md=state.battle_plan_md,
        agent_specs=state.tick_agent_specs,
        branch_contexts=_branch_context_items(state),
        model=getattr(model_provider, "model", None),
        model_provider=model_provider,
    )
    state.planned_branch_executions = branch_executions
    state.planned_agent_params = _flatten_branch_executions(branch_executions)
    state.agent_param_source = "llm"
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
            "planned_agents": _planned_agent_log_items(state.planned_agent_params),
            "error": trace.error,
        },
    )
    return state


def _run_output_seed_agent_parameter_planning_node(state: BattlePlannerState) -> BattlePlannerState:
    seed = load_agent_parameter_planning_output_seed(iteration_index=state.iteration_index)
    branch_executions = [item.model_copy(deep=True) for item in seed.branch_executions]
    planned = _flatten_branch_executions(branch_executions)
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
        },
    )
    state.planned_branch_executions = branch_executions
    state.planned_agent_params = planned
    state.agent_param_source = "run_output_seed"
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
                "trace_summary": seed.trace_summary,
                "branch_executions": [item.model_dump(mode="json") for item in branch_executions],
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
            "fallback": False,
            "planned_agents": _planned_agent_log_items(planned),
            "error": None,
        },
    )
    return state


def _flatten_branch_executions(
    branch_executions: list[SchemeBranchExecutionSpec],
) -> list[TickAgentParams]:
    return [
        agent.model_copy(deep=True)
        for branch_execution in branch_executions
        for agent in branch_execution.planned_agent_params
    ]


def _branch_context_items(state: BattlePlannerState) -> list[dict]:
    if state.task_context is None:
        return []
    return [
        {
            "branch_id": branch.branch_id,
            "name": branch.name,
            "description": branch.description,
            "human": branch.human.model_dump(mode="json"),
        }
        for branch in state.task_context.branches
    ]


def _planned_agent_log_items(planned: list[TickAgentParams]) -> list[dict]:
    return [
        {
            "agent_instance_id": item.agent_instance_id,
            "agent_name": item.agent_name,
            "agent_params": item.params,
        }
        for item in planned
    ]
