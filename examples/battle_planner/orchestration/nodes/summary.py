from __future__ import annotations

from typing import Any

from battle_planner.agents.summary_generation import generate_summary
from battle_planner.config import config
from battle_planner.data.models import (
    AgentExecutionSummary,
    SummaryEvaluation,
    TargetObjectiveSummary,
)
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def summary_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "summary",
        iteration_index=state.iteration_index,
        simulation_ready=state.simulation_result is not None,
        evaluation_ready=state.evaluation_report is not None,
    )
    if state.simulation_result is None or state.evaluation_report is None:
        state.mark_error("summary requires simulation_result and evaluation_report")
        log_node_error("summary", state.error or "missing inputs", iteration_index=state.iteration_index)
        return state
    summary_evaluation = build_summary_evaluation(state)
    output, trace = generate_summary(
        scenario_understanding_md=state.scenario_understanding_md,
        battle_plan_md=state.battle_plan_md,
        planned_agent_params=state.planned_agent_params,
        simulation_result=state.simulation_result,
        evaluation_report=state.evaluation_report,
        summary_evaluation=summary_evaluation,
    )
    state.summary_evaluation = summary_evaluation
    state.summary_md = output
    state.add_trace(trace)
    state.cur_stage = "complete"
    log_node_end(
        "summary",
        iteration_index=state.iteration_index,
        fallback=trace.fallback_used,
        output_chars=len(output),
        objective_achieved=summary_evaluation.objective_achieved,
        inactive_agents=summary_evaluation.inactive_agents,
        error=trace.error,
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
    target_results = _as_dict(callbacks.get(callback_instance_id))
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
    for callback in state.callback_params:
        if callback.name == "target_statistic" and callback.callback_instance_id:
            return callback.callback_instance_id
    return config.simulation.target_statistic.callback_instance_id


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
