from __future__ import annotations

from typing import Any

from battle_planner.agents.summary_generation import generate_summary
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.run_output_seed import load_summary_generation_output_seed


def summary_generation_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.SUMMARY_GENERATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "simulation_ready": state.simulation_result is not None,
            "evaluation_ready": state.evaluation_summary is not None,
            "simulation_count": len(state.simulation_results),
        },
    )
    if state.simulation_result is None:
        state.mark_error("summary requires simulation_result")
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.ERROR,
            level=EventLevels.NODE,
            iteration_index=state.iteration_index,
            payload={"error": state.error or "missing inputs"},
        )
        return state
    callback_reports = _callback_reports(state.simulation_result)
    if settings.LLM_MODE == LLMMode.OFFLINE and settings.OUTPUT_SEED:
        seed = load_summary_generation_output_seed(iteration_index=state.iteration_index)
        summary_evaluation = seed.summary_evaluation
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
        output = seed.summary_md
        trace = identity_trace(
            WorkflowStages.SUMMARY_GENERATION,
            input_value={
                "source": "run_output_seed",
                "seed_id": settings.OUTPUT_SEED,
                "runtime_iteration_index": state.iteration_index,
                "evaluation_summary": state.evaluation_summary.model_dump(mode="json")
                if state.evaluation_summary
                else None,
                "summary_evaluation": summary_evaluation.model_dump(mode="json"),
                **seed.trace_summary,
            },
            output_value={
                "summary_md": output,
                "trace_summary": seed.trace_summary,
            },
        )
    else:
        output, trace, summary_evaluation = generate_summary(
            scenario_understanding_md=state.scenario_understanding_md,
            battle_plan_md=state.battle_plan_md,
            planned_agent_params=state.planned_agent_params,
            simulation_result=state.simulation_result,
            callback_reports=callback_reports,
            evaluation_summary=state.evaluation_summary,
        )
        output = _append_session_status_placeholder(output)
    state.summary_evaluation = summary_evaluation
    state.summary_md = output
    state.add_trace(trace)
    state.cur_stage = WorkflowStages.COMPLETE
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "fallback": trace.fallback_used,
            "output_chars": len(output),
            "objective_achieved": summary_evaluation.objective_achieved,
            "inactive_agents": summary_evaluation.inactive_agents,
            "error": trace.error,
        },
    )
    return state


def _append_session_status_placeholder(summary_md: str) -> str:
    # TODO: 添加基于历史迭代趋势的 session 现状分析。
    placeholder = "\n".join(
        [
            "",
            "## Session 现状分析",
            "- 当前为正式模型占位文本，后续结合历史轮次与多局仿真结果生成。",
        ]
    )
    return f"{summary_md.rstrip()}\n{placeholder}"


def _callback_reports(simulation_result: Any) -> dict[str, Any]:
    runner_report = _as_dict(simulation_result.raw_summary.get("runner_report"))
    return _as_dict(runner_report.get("callbacks"))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
