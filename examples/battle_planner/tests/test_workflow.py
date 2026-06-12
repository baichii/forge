"""Multi-iteration workflow smoke for K1 -> K2 -> K3 loop wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState, build_initial_state
from battle_planner.orchestration.workflow.zc_lite_baseline import ZcLiteBaselineWorkflow
from battle_planner.orchestration.workflow_entropy import build_workflow
from battle_planner.workspace.local.run_input_seed import build_local_task_run


@dataclass
class WorkflowLoopResult:
    states: list[BattlePlannerState] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    stop_reason: str = "max_iterations"


def run_workflow_loop(*, max_iterations: int | None = None) -> WorkflowLoopResult:
    task_run = build_local_task_run()
    workflow = build_workflow(task_run.options.workflow_name)
    iterations = max_iterations if max_iterations is not None else task_run.options.max_iterations
    states: list[BattlePlannerState] = []
    history: list[dict[str, Any]] = []
    status = "completed"
    stop_reason = "max_iterations"

    for iteration_index in range(iterations):
        initial_state = build_initial_state(task_run).model_copy(
            update={"iteration_index": iteration_index, "history": list(history)}
        )
        state = workflow.run(initial_state)
        if state.cur_stage == WorkflowStages.COMPLETE:
            history.append(build_history_item(state))
            state.history = list(history)
        states.append(state)

        if state.error:
            status = "failed"
            stop_reason = "error"
            break

    return WorkflowLoopResult(states=states, history=history, status=status, stop_reason=stop_reason)


def test_workflow_loop_smoke(monkeypatch) -> None:
    """验证离线 workflow 能连续完成多轮迭代。"""

    _force_offline_llm_mode(monkeypatch)

    result = run_workflow_loop(max_iterations=2)
    states = result.states

    assert len(states) == 2
    assert all(state.cur_stage == WorkflowStages.COMPLETE for state in states)
    assert all(state.evaluation_report is not None for state in states)
    assert all(state.summary_md for state in states)
    assert states[0].planned_agent_params != states[1].planned_agent_params
    assert states[0].battle_plan_md != states[1].battle_plan_md
    assert len(result.history) == 2
    assert _trace_source(states[1], WorkflowStages.BATTLE_PLAN_GENERATION) == "run_output_seed"


def test_workflow_entropy_uses_configured_default() -> None:
    """验证 workflow 工厂能使用默认 workflow 配置。"""

    workflow = build_workflow()

    assert isinstance(workflow, ZcLiteBaselineWorkflow)


def test_workflow_entropy_accepts_option_workflow_name() -> None:
    """验证 workflow 工厂能按显式名称构建流程。"""

    task_run = build_local_task_run()
    task_run.options.workflow_name = "zc_lite_baseline"

    workflow = build_workflow(task_run.options.workflow_name)

    assert isinstance(workflow, ZcLiteBaselineWorkflow)


def test_workflow_entropy_rejects_unknown_workflow_name(monkeypatch) -> None:
    """验证 workflow 工厂能拒绝未知流程名称。"""

    monkeypatch.setattr(settings, "WORKFLOW_NAME", "missing")

    with pytest.raises(ValueError, match="Unknown battle planner workflow"):
        build_workflow()


def _force_offline_llm_mode(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_MODE", LLMMode.OFFLINE)
    monkeypatch.setattr(settings, "SIM_MAX_DECISION_STEPS", 70)


def _trace_source(state: BattlePlannerState, node_name: str) -> str:
    for trace in state.llm_traces:
        if trace.node_name == node_name and isinstance(trace.parsed_output, dict):
            trace_summary = trace.parsed_output.get("trace_summary")
            if isinstance(trace_summary, dict):
                return str(trace_summary.get("source") or "")
    return ""
