from __future__ import annotations

from typing import Any

from battle_planner.model import (
    LLMTrace,
    RunIterationOutputSpec,
    RunIterationTagSpec,
    RunMetricAggregateSpec,
    RunSimulationRecordSpec,
    RunTextSummarySpec,
    SchemeSpec,
)
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def build_run_iteration_output(state: BattlePlannerState) -> RunIterationOutputSpec:
    """将 workflow state 转换为单轮运行输出。"""

    status = "running"
    if state.error or state.cur_stage == WorkflowStages.ERROR:
        status = "failed"
    elif state.cur_stage == WorkflowStages.COMPLETE:
        status = "completed"
    elif state.cur_stage == WorkflowStages.START:
        status = "pending"

    summary = _compact_text(state.summary_md)
    overall_summary = (
        RunTextSummarySpec(label="overall", title="总体摘要", summary=summary) if summary else None
    )

    effect_summary = None
    decision_summary = None
    if state.summary_evaluation is not None:
        achieved_text = "目标已达成" if state.summary_evaluation.objective_achieved else "目标未达成"
        effect_summary = RunTextSummarySpec(
            label="effect",
            title="效果摘要",
            summary=(
                f"{achieved_text}，"
                f"未执行 agent {len(state.summary_evaluation.inactive_agents)} 个，"
                f"风险提示 {len(state.summary_evaluation.warnings)} 条。"
            ),
        )
        if state.summary_evaluation.advice:
            decision_summary = RunTextSummarySpec(
                label="decision",
                title="决策建议",
                summary=state.summary_evaluation.advice,
            )

    report_summary = None
    if state.evaluation_summary is not None:
        report_summary = RunTextSummarySpec(
            label="report",
            title="仿真报告摘要",
            summary=(
                f"完成 {state.evaluation_summary.case_count} 次仿真验证，"
                f"成功率 {state.evaluation_summary.success_rate:.2f}，"
                f"平均得分 {state.evaluation_summary.mean_score:.2f}。"
            ),
        )

    simulation_runs = [
        RunSimulationRecordSpec(
            simulation_index=simulation_index,
            seed=_extract_simulation_seed(simulation_result),
            simulation_result=simulation_result,
            summary=RunTextSummarySpec(
                label="simulation",
                title=f"仿真 {simulation_index + 1}",
                summary=(
                    f"执行 {simulation_result.steps} 步，"
                    f"结束状态 {'已结束' if simulation_result.done else '未结束'}，"
                    f"指标 {len(simulation_result.metrics)} 项。"
                ),
            ),
        )
        for simulation_index, simulation_result in enumerate(state.simulation_results)
    ]

    return RunIterationOutputSpec(
        iteration_index=state.iteration_index,
        status=status,
        iteration_tags=_build_iteration_tags(state.llm_traces),
        overall_summary=overall_summary,
        effect_summary=effect_summary,
        report_summary=report_summary,
        decision_summary=decision_summary,
        scheme=SchemeSpec(
            scheme_id=state.iteration_index + 1,
            run_id=state.run_id or "",
            branch_executions=state.planned_branch_executions,
            planned_agent_params=state.planned_agent_params,
            callback_params=state.callback_params,
        ),
        simulation_runs=simulation_runs,
        metric_aggregates=_build_metric_aggregates(
            state.evaluation_summary.metric_summary if state.evaluation_summary else {}
        ),
    )


def _build_iteration_tags(llm_traces: list[LLMTrace]) -> list[RunIterationTagSpec]:
    for trace in reversed(llm_traces):
        if not isinstance(trace.parsed_output, dict):
            continue
        trace_summary = _as_dict(trace.parsed_output.get("trace_summary"))
        tags = trace_summary.get("iteration_tags")
        if isinstance(tags, list):
            return [RunIterationTagSpec.model_validate(tag) for tag in tags if isinstance(tag, dict)]
    return []


def _extract_simulation_seed(simulation_result: Any) -> int | None:
    runner_report = _as_dict(simulation_result.raw_summary.get("runner_report"))
    env_report = _as_dict(runner_report.get("env"))
    seed = env_report.get("seed")
    return seed if isinstance(seed, int) else None


def _compact_text(text: str, *, max_length: int = 240) -> str:
    lines = [line.strip().lstrip("#").strip() for line in text.splitlines()]
    compacted = " ".join(line for line in lines if line)
    if len(compacted) <= max_length:
        return compacted
    return f"{compacted[: max_length - 3]}..."


def _build_metric_aggregates(metric_summary: dict[str, Any]) -> list[RunMetricAggregateSpec]:
    aggregates: list[RunMetricAggregateSpec] = []
    for payload in metric_summary.values():
        if not isinstance(payload, dict):
            continue
        aggregates.append(RunMetricAggregateSpec.model_validate(payload))
    return aggregates


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
