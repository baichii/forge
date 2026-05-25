"""Multi-iteration workflow smoke for K1 -> K2 -> K3 loop wiring."""

from __future__ import annotations

from battle_planner.config import ModelProfile, config
from battle_planner.orchestration.session import (
    BattlePlannerSession,
    BattlePlannerSessionResult,
    IterationView,
)
from battle_planner.orchestration.state.state import BattlePlannerState


def run_workflow_session(*, max_iterations: int | None = None) -> BattlePlannerSessionResult:
    return BattlePlannerSession(max_iterations=max_iterations).run()


def main() -> None:
    result = run_workflow_session()
    print("Battle planner workflow loop finished")
    print(f"session_id: {result.session_id}")
    print(f"status: {result.status}")
    print(f"stop_reason: {result.stop_reason}")
    print(f"configured_iterations: {config.workflow.max_iterations}")
    print(f"completed_iterations: {len(result.view.iterations)}")
    print("")

    for iteration in result.view.iterations:
        _print_iteration(iteration)

    print("iteration summary")
    print(
        "index | preset | score | achieved | destroyed | health_initial | "
        "health_current | health_delta | damage_ratio | requested_wp"
    )
    for iteration in result.view.iterations:
        print(
            " | ".join(
                [
                    str(iteration.iteration_index),
                    str(iteration.agent_param_preset_id or ""),
                    str(iteration.score),
                    str(iteration.objective_achieved),
                    str(iteration.target_destroyed_count),
                    str(iteration.target_initial_health),
                    str(iteration.target_current_health),
                    str(iteration.target_health_delta),
                    str(iteration.target_damage_ratio),
                    str(iteration.requested_weapon_count),
                ]
            )
        )


def test_workflow_loop_smoke(monkeypatch) -> None:
    _force_offline_display_mode(monkeypatch)

    result = run_workflow_session()
    states = result.states

    assert len(states) == 2
    assert all(state.cur_stage == "complete" for state in states)
    assert all(state.evaluation_report is not None for state in states)
    assert all(state.summary_md for state in states)
    assert states[0].agent_param_preset_id != states[1].agent_param_preset_id
    assert len(result.history) == 2
    assert len(result.view.iterations) == 2
    assert "历史迭代反馈" in _trace_content(states[1], "battle_plan_generation")


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


def _print_iteration(iteration: IterationView) -> None:
    print(f"iteration_index: {iteration.iteration_index}")
    print(f"- agent_param_preset_id: {iteration.agent_param_preset_id}")
    print(f"- score: {iteration.score}")
    print(f"- objective_achieved: {iteration.objective_achieved}")
    print(f"- target_destroyed_count: {iteration.target_destroyed_count}")
    print(f"- target_initial_health: {iteration.target_initial_health}")
    print(f"- target_current_health: {iteration.target_current_health}")
    print(f"- target_health_delta: {iteration.target_health_delta}")
    print(f"- target_damage_ratio: {iteration.target_damage_ratio}")
    print(f"- requested_weapon_count: {iteration.requested_weapon_count}")
    print(f"- key_events: {len(iteration.key_events)}")
    print("- summary_excerpt:")
    for line in _summary_excerpt(iteration.summary_excerpt):
        print(f"  {line}")
    if iteration.error:
        print(f"- error: {iteration.error}")
    print("")


def _trace_content(state: BattlePlannerState, node_name: str) -> str:
    for trace in state.llm_traces:
        if trace.node_name == node_name and trace.input_messages:
            return str(trace.input_messages[-1].get("content") or "")
    return ""


def _summary_excerpt(summary_md: str, *, max_lines: int = 12) -> list[str]:
    lines = [line for line in summary_md.splitlines() if line.strip()]
    return lines[:max_lines]


if __name__ == "__main__":
    main()
