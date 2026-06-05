"""Multi-iteration workflow smoke for K1 -> K2 -> K3 loop wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from battle_planner.config import ModelProfile, config
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.orchestration.workflow.zc_lite_baseline import ZcLiteBaselineWorkflow
from battle_planner.orchestration.workflow_entropy import WorkflowEntropy, build_workflow


@dataclass
class WorkflowLoopResult:
    states: list[BattlePlannerState] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    stop_reason: str = "max_iterations"


def run_workflow_loop(*, max_iterations: int | None = None) -> WorkflowLoopResult:
    workflow = ZcLiteBaselineWorkflow()
    iterations = max_iterations if max_iterations is not None else config.workflow.max_iterations
    states: list[BattlePlannerState] = []
    history: list[dict[str, Any]] = []
    status = "completed"
    stop_reason = "max_iterations"

    for iteration_index in range(iterations):
        state = workflow.run(BattlePlannerState(iteration_index=iteration_index, history=list(history)))
        if state.cur_stage == "complete":
            history.append(build_history_item(state))
            state.history = list(history)
        states.append(state)

        if state.error:
            status = "failed"
            stop_reason = "error"
            break

    return WorkflowLoopResult(states=states, history=history, status=status, stop_reason=stop_reason)


def main() -> None:
    result = run_workflow_loop()
    print("Battle planner workflow loop finished")
    print(f"status: {result.status}")
    print(f"stop_reason: {result.stop_reason}")
    print(f"configured_iterations: {config.workflow.max_iterations}")
    print(f"completed_iterations: {len(result.states)}")
    print("")

    for state in result.states:
        _print_iteration(state)

    print("iteration summary")
    print(
        "index | preset | score | achieved | destroyed | health_initial | "
        "health_current | health_delta | damage_ratio | requested_wp"
    )
    for state in result.states:
        metrics = _mission_metrics(state)
        print(
            " | ".join(
                [
                    str(state.iteration_index),
                    str(state.agent_param_preset_id or ""),
                    str(state.evaluation_report.score if state.evaluation_report else None),
                    str(metrics.get("objective_achieved")),
                    str(metrics.get("target_destroyed_count")),
                    str(metrics.get("target_initial_health")),
                    str(metrics.get("target_current_health")),
                    str(metrics.get("target_health_delta")),
                    str(metrics.get("target_damage_ratio")),
                    str(metrics.get("requested_weapon_count")),
                ]
            )
        )


def test_workflow_loop_smoke(monkeypatch) -> None:
    _force_offline_display_mode(monkeypatch)

    result = run_workflow_loop()
    states = result.states

    assert len(states) == 2
    assert all(state.cur_stage == "complete" for state in states)
    assert all(state.evaluation_report is not None for state in states)
    assert all(state.summary_md for state in states)
    assert states[0].agent_param_preset_id != states[1].agent_param_preset_id
    assert len(result.history) == 2
    assert "历史迭代反馈" in _trace_content(states[1], "battle_plan_generation")


def test_workflow_entropy_builds_workflow_by_name() -> None:
    assert ZcLiteBaselineWorkflow.name == "zc_lite_baseline"

    workflow = build_workflow("zc_lite_baseline")

    assert isinstance(workflow, ZcLiteBaselineWorkflow)
    assert WorkflowEntropy.build_workflow("zc_lite_baseline").name == "zc_lite_baseline"

    with pytest.raises(ValueError, match="Unknown battle planner workflow"):
        build_workflow("missing")


def _force_offline_display_mode(monkeypatch) -> None:
    config.model.profiles.setdefault(
        "offline",
        ModelProfile(name="offline", provider="offline", model_name="offline"),
    )
    monkeypatch.setattr(config.model, "selected", "offline")
    monkeypatch.setattr(config.workflow, "display_mode", True)
    monkeypatch.setattr(config.workflow, "max_iterations", 2)
    monkeypatch.setattr(config.workflow, "save_artifacts", False)
    monkeypatch.setattr(config.simulation, "max_decision_steps", 70)


def _print_iteration(state: BattlePlannerState) -> None:
    metrics = _mission_metrics(state)
    print(f"iteration_index: {state.iteration_index}")
    print(f"- agent_param_preset_id: {state.agent_param_preset_id}")
    print(f"- score: {state.evaluation_report.score if state.evaluation_report else None}")
    print(f"- objective_achieved: {metrics.get('objective_achieved')}")
    print(f"- target_destroyed_count: {metrics.get('target_destroyed_count')}")
    print(f"- target_initial_health: {metrics.get('target_initial_health')}")
    print(f"- target_current_health: {metrics.get('target_current_health')}")
    print(f"- target_health_delta: {metrics.get('target_health_delta')}")
    print(f"- target_damage_ratio: {metrics.get('target_damage_ratio')}")
    print(f"- requested_weapon_count: {metrics.get('requested_weapon_count')}")
    print("- summary_excerpt:")
    for line in _summary_excerpt(state.summary_md):
        print(f"  {line}")
    if state.error:
        print(f"- error: {state.error}")
    print("")


def _trace_content(state: BattlePlannerState, node_name: str) -> str:
    for trace in state.llm_traces:
        if trace.node_name == node_name and trace.input_messages:
            return str(trace.input_messages[-1].get("content") or "")
    return ""


def _summary_excerpt(summary_md: str, *, max_lines: int = 12) -> list[str]:
    lines = [line for line in summary_md.splitlines() if line.strip()]
    return lines[:max_lines]


def _mission_metrics(state: BattlePlannerState) -> dict[str, Any]:
    if state.evaluation_report is None:
        return {}
    return dict(state.evaluation_report.mission_metrics)


if __name__ == "__main__":
    main()
