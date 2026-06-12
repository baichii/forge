from __future__ import annotations

from typing import Any

from battle_planner.agents.summary_generation import generate_summary
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.trace import identity_trace
from battle_planner.model import (
    AgentExecutionSummary,
    SummaryEvaluation,
    TargetObjectiveSummary,
)
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.plan_presets import load_plan_preset
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
            "evaluation_ready": state.evaluation_report is not None,
            "simulation_count": len(state.simulation_results),
            "evaluation_count": len(state.evaluation_reports),
        },
    )
    if state.simulation_result is None or state.evaluation_report is None:
        state.mark_error("summary requires simulation_result and evaluation_report")
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.ERROR,
            level=EventLevels.NODE,
            iteration_index=state.iteration_index,
            payload={"error": state.error or "missing inputs"},
        )
        return state
    summary_evaluation = build_summary_evaluation(state)
    if settings.LLM_MODE == LLMMode.OFFLINE and settings.OUTPUT_SEED:
        seed = load_summary_generation_output_seed(iteration_index=state.iteration_index)
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
                "objective_achieved": summary_evaluation.objective_achieved,
                "evaluation_summary": state.evaluation_summary.model_dump(mode="json")
                if state.evaluation_summary
                else None,
                **seed.trace_summary,
            },
            output_value={
                "summary_md": output,
                "trace_summary": seed.trace_summary,
            },
        )
    else:
        output, trace = generate_summary(
            scenario_understanding_md=state.scenario_understanding_md,
            battle_plan_md=state.battle_plan_md,
            planned_agent_params=state.planned_agent_params,
            simulation_result=state.simulation_result,
            evaluation_report=state.evaluation_report,
            evaluation_summary=state.evaluation_summary,
            summary_evaluation=summary_evaluation,
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
            "mean_score": state.evaluation_summary.mean_score if state.evaluation_summary else None,
            "inactive_agents": summary_evaluation.inactive_agents,
            "error": trace.error,
        },
    )
    return state


def build_summary_evaluation(state: BattlePlannerState) -> SummaryEvaluation:
    if state.simulation_result is None:
        raise ValueError("build_summary_evaluation requires simulation_result")

    objective = ""
    if state.planner_knowledge_pack is not None:
        objective = state.planner_knowledge_pack.planning_goal.objective

    callback_instance_id = _target_statistic_callback_id(state)
    runner_report = _as_dict(state.simulation_result.raw_summary.get("runner_report"))
    callbacks = _as_dict(runner_report.get("callbacks"))
    target_results = _target_statistic_targets(_as_dict(callbacks.get(callback_instance_id)))
    warnings: list[str] = []

    if not target_results:
        warnings.append(f"未找到 {callback_instance_id} callback 结果，无法判断目标达成情况。")

    target_status = [
        _build_target_summary(target_id=target_id, payload=_as_dict(payload))
        for target_id, payload in target_results.items()
    ]
    objective_achieved = bool(target_status) and all(item.achieved for item in target_status)

    agent_execution = [
        _build_agent_execution_summary(_as_dict(agent)) for agent in _as_list(runner_report.get("agents"))
    ]
    inactive_agents = [item.agent_instance_id for item in agent_execution if not item.executed]
    if inactive_agents:
        warnings.append(
            "存在未执行动作的 agent，可能原因：时间窗口未到、目标已消失、重复打击、单位/目标匹配失败。"
        )

    return SummaryEvaluation(
        iteration_index=state.iteration_index,
        objective=objective,
        objective_achieved=objective_achieved,
        target_status=target_status,
        agent_execution=agent_execution,
        inactive_agents=inactive_agents,
        warnings=warnings,
        advice=_build_iteration_advice(
            objective_achieved=objective_achieved,
            inactive_agents=inactive_agents,
        ),
    )


def _target_statistic_callback_id(state: BattlePlannerState) -> str:
    plan_preset = load_plan_preset(state.plan_id, scenario_name=state.scenario_name)
    return plan_preset.objective_callback_instance_id


def _target_statistic_targets(callback_result: dict[str, Any]) -> dict[str, Any]:
    targets = _as_dict(_as_dict(callback_result.get("payload")).get("targets"))
    if targets:
        return targets
    return callback_result


def _build_target_summary(*, target_id: str, payload: dict[str, Any]) -> TargetObjectiveSummary:
    initial = _as_dict(payload.get("initial"))
    current = _as_dict(payload.get("current"))
    delta = _as_dict(payload.get("delta"))
    alive = bool(payload.get("alive", True))
    return TargetObjectiveSummary(
        target_id=target_id,
        alive=alive,
        initial_health=_number_or_none(initial.get("health")),
        current_health=_number_or_none(current.get("health")),
        health_delta=_number_or_none(delta.get("health")),
        health_percent_delta=_number_or_none(delta.get("health_percent")),
        achieved=not alive,
    )


def _build_agent_execution_summary(agent: dict[str, Any]) -> AgentExecutionSummary:
    action_count = int(agent.get("action_count") or 0)
    executed = action_count > 0
    return AgentExecutionSummary(
        agent_instance_id=str(agent.get("agent_instance_id") or ""),
        agent_name=str(agent.get("agent_name") or ""),
        side=str(agent.get("side") or ""),
        action_count=action_count,
        executed=executed,
        first_active_step=_int_or_none(agent.get("first_active_step")),
        finished_step=_int_or_none(agent.get("finished_step")),
        issue="" if executed else "未执行动作，需检查时间窗口、目标消失、重复打击或单位/目标匹配。",
    )


def _build_iteration_advice(*, objective_achieved: bool, inactive_agents: list[str]) -> str:
    if objective_achieved and inactive_agents:
        return "目标已达成，但存在未执行 agent；下一轮先检查时间窗口和重复打击，再考虑降低火力。"
    if objective_achieved:
        return "目标已达成，下一轮可降低火力寻找临界条件。"
    if inactive_agents:
        return "目标未达成且存在未执行 agent；下一轮优先检查时间窗口、目标接地和单位匹配。"
    return "目标未达成，下一轮可增强火力或调整打击时序。"


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


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number_or_none(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int | float) else None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None
