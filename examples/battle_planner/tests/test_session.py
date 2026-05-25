from __future__ import annotations

import json

from battle_planner.config import ModelProfile, config
from battle_planner.orchestration.session import BattlePlannerSession


def test_session_runs_iterations_and_builds_web_view(monkeypatch) -> None:
    _force_offline_display_mode(monkeypatch, max_iterations=2, save_artifacts=False)

    result = BattlePlannerSession().run()

    assert result.status == "completed"
    assert result.stop_reason == "max_iterations"
    assert len(result.states) == 2
    assert len(result.history) == 2
    assert len(result.view.iterations) == 2
    assert result.view.iterations[0].score is not None
    assert result.view.iterations[0].target_health_delta is not None
    assert result.view.iterations[0].requested_weapon_count is not None
    assert "历史迭代反馈" in _trace_content(result.states[1], "battle_plan_generation")


def test_session_file_store_writes_artifacts(monkeypatch, tmp_path) -> None:
    _force_offline_display_mode(monkeypatch, max_iterations=1, save_artifacts=True)
    monkeypatch.setattr(config.workflow, "artifact_dir", str(tmp_path))

    result = BattlePlannerSession(session_id="test-session").run()
    session_dir = tmp_path / "sessions" / result.session_id
    iteration_dir = session_dir / "iterations" / "000"

    assert (session_dir / "session.json").exists()
    assert (session_dir / "events.jsonl").exists()
    assert (iteration_dir / "state.json").exists()
    assert (iteration_dir / "plan.md").exists()
    assert (iteration_dir / "summary.md").exists()
    assert (iteration_dir / "evaluation.json").exists()
    assert (iteration_dir / "runner_report.json").exists()

    session_payload = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_payload["session_id"] == "test-session"
    assert session_payload["iterations"][0]["iteration_index"] == 0


def _force_offline_display_mode(monkeypatch, *, max_iterations: int, save_artifacts: bool) -> None:
    config.model.profiles.setdefault(
        "offline",
        ModelProfile(name="offline", provider="offline", model_name="offline"),
    )
    monkeypatch.setattr(config.model, "selected", "offline")
    monkeypatch.setattr(config.workflow, "display_mode", True)
    monkeypatch.setattr(config.workflow, "max_iterations", max_iterations)
    monkeypatch.setattr(config.workflow, "save_artifacts", save_artifacts)
    monkeypatch.setattr(config.simulation, "max_decision_steps", 70)


def _trace_content(state, node_name: str) -> str:
    for trace in state.llm_traces:
        if trace.node_name == node_name and trace.input_messages:
            return str(trace.input_messages[-1].get("content") or "")
    return ""
