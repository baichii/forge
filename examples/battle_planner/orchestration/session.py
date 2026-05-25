from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from battle_planner.config import config
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.orchestration.workflow import BattlePlannerDemoWorkflow
from pydantic import BaseModel, Field


class IterationView(BaseModel):
    """Lightweight iteration view for terminal output and future Web UI."""

    iteration_index: int
    status: str = ""
    agent_param_preset_id: str | None = None
    score: float | None = None
    objective_achieved: bool | None = None
    target_initial_health: int | float | None = None
    target_current_health: int | float | None = None
    target_health_delta: int | float | None = None
    target_damage_ratio: int | float | None = None
    target_destroyed_count: int | float | None = None
    requested_weapon_count: int | float | None = None
    inactive_agent_count: int | float | None = None
    advice: str = ""
    summary_excerpt: str = ""
    key_events: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class BattlePlannerSessionView(BaseModel):
    """Session-level snapshot intended to be read by a simple Web UI."""

    session_id: str
    status: str = "running"
    current_iteration: int = 0
    max_iterations: int = 0
    stop_reason: str = ""
    iterations: list[IterationView] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: _now_iso())
    updated_at: str = Field(default_factory=lambda: _now_iso())


class BattlePlannerSessionResult(BaseModel):
    session_id: str
    states: list[BattlePlannerState] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    view: BattlePlannerSessionView
    status: str = "completed"
    stop_reason: str = "max_iterations"


class NoopSessionStore:
    def start_session(self, view: BattlePlannerSessionView) -> None:
        return None

    def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        return None

    def save_iteration(self, session_id: str, state: BattlePlannerState, view: IterationView) -> None:
        return None

    def update_session_view(self, view: BattlePlannerSessionView) -> None:
        return None

    def finish_session(self, view: BattlePlannerSessionView) -> None:
        return None


class FileSessionStore(NoopSessionStore):
    def __init__(self, artifact_dir: str | Path):
        self.artifact_dir = Path(artifact_dir)

    def start_session(self, view: BattlePlannerSessionView) -> None:
        self._session_dir(view.session_id).mkdir(parents=True, exist_ok=True)
        self.update_session_view(view)
        self.append_event(view.session_id, {"event": "session_start", "status": view.status})

    def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        payload = {"ts": _now_iso(), **event}
        path = self._session_dir(session_id) / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, default=str))
            file.write("\n")

    def save_iteration(self, session_id: str, state: BattlePlannerState, view: IterationView) -> None:
        iteration_dir = self._session_dir(session_id) / "iterations" / f"{state.iteration_index:03d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)
        _write_json(iteration_dir / "state.json", state.model_dump(mode="json"))
        (iteration_dir / "plan.md").write_text(state.battle_plan_md, encoding="utf-8")
        (iteration_dir / "summary.md").write_text(state.summary_md, encoding="utf-8")
        _write_json(
            iteration_dir / "evaluation.json",
            state.evaluation_report.model_dump(mode="json") if state.evaluation_report else {},
        )
        _write_json(iteration_dir / "runner_report.json", _runner_report_payload(state))
        self.append_event(
            session_id,
            {
                "event": "iteration_saved",
                "iteration_index": state.iteration_index,
                "status": view.status,
            },
        )

    def update_session_view(self, view: BattlePlannerSessionView) -> None:
        view.updated_at = _now_iso()
        _write_json(self._session_dir(view.session_id) / "session.json", view.model_dump(mode="json"))

    def finish_session(self, view: BattlePlannerSessionView) -> None:
        self.update_session_view(view)
        self.append_event(
            view.session_id,
            {"event": "session_finish", "status": view.status, "stop_reason": view.stop_reason},
        )

    def _session_dir(self, session_id: str) -> Path:
        return self.artifact_dir / "sessions" / session_id


class BattlePlannerSession:
    """Owns multi-iteration battle planner lifecycle around the single-run workflow."""

    def __init__(
        self,
        *,
        session_id: str | None = None,
        workflow: BattlePlannerDemoWorkflow | None = None,
        store: NoopSessionStore | FileSessionStore | None = None,
        max_iterations: int | None = None,
    ):
        self.session_id = session_id or f"bp-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        self.workflow = workflow or BattlePlannerDemoWorkflow()
        self.store = store if store is not None else _default_store()
        self.max_iterations = max_iterations if max_iterations is not None else config.workflow.max_iterations

    def run(self) -> BattlePlannerSessionResult:
        states: list[BattlePlannerState] = []
        history: list[dict[str, Any]] = []
        status = "completed"
        stop_reason = "max_iterations"
        view = BattlePlannerSessionView(
            session_id=self.session_id,
            status="running",
            max_iterations=self.max_iterations,
        )
        self.store.start_session(view)

        for iteration_index in range(self.max_iterations):
            self.store.append_event(
                self.session_id,
                {"event": "iteration_start", "iteration_index": iteration_index},
            )
            state = self.run_iteration(iteration_index=iteration_index, history=history)
            if state.cur_stage == "complete":
                history.append(build_history_item(state))
                state.history = list(history)
            states.append(state)

            iteration_view = build_iteration_view(state)
            view.iterations.append(iteration_view)
            view.current_iteration = len(view.iterations)
            self.store.save_iteration(self.session_id, state, iteration_view)
            self.store.update_session_view(view)
            self.store.append_event(
                self.session_id,
                {
                    "event": "iteration_end",
                    "iteration_index": iteration_index,
                    "status": iteration_view.status,
                    "error": state.error,
                },
            )

            if state.error:
                status = "failed"
                stop_reason = "error"
                break

        view.status = status
        view.stop_reason = stop_reason
        self.store.finish_session(view)
        return BattlePlannerSessionResult(
            session_id=self.session_id,
            states=states,
            history=history,
            view=view,
            status=status,
            stop_reason=stop_reason,
        )

    def run_iteration(self, *, iteration_index: int, history: list[dict[str, Any]]) -> BattlePlannerState:
        return self.workflow.run(
            BattlePlannerState(iteration_index=iteration_index, history=list(history))
        )


def build_iteration_view(state: BattlePlannerState) -> IterationView:
    metrics = _mission_metrics(state)
    summary_evaluation = state.summary_evaluation
    objective_achieved = metrics.get("objective_achieved")
    if objective_achieved is None and summary_evaluation is not None:
        objective_achieved = summary_evaluation.objective_achieved

    return IterationView(
        iteration_index=state.iteration_index,
        status="failed" if state.error else state.cur_stage,
        agent_param_preset_id=state.agent_param_preset_id,
        score=state.evaluation_report.score if state.evaluation_report else None,
        objective_achieved=_bool_or_none(objective_achieved),
        target_initial_health=metrics.get("target_initial_health"),
        target_current_health=metrics.get("target_current_health"),
        target_health_delta=metrics.get("target_health_delta"),
        target_damage_ratio=metrics.get("target_damage_ratio"),
        target_destroyed_count=metrics.get("target_destroyed_count"),
        requested_weapon_count=metrics.get("requested_weapon_count"),
        inactive_agent_count=metrics.get("inactive_agent_count"),
        advice=_advice(state),
        summary_excerpt=_summary_excerpt(state.summary_md),
        key_events=_key_events(state),
        error=state.error,
    )


def _default_store() -> NoopSessionStore | FileSessionStore:
    if not config.workflow.save_artifacts:
        return NoopSessionStore()
    return FileSessionStore(config.workflow.artifact_dir)


def _mission_metrics(state: BattlePlannerState) -> dict[str, Any]:
    if state.evaluation_report is None:
        return {}
    return dict(state.evaluation_report.mission_metrics)


def _advice(state: BattlePlannerState) -> str:
    if state.evaluation_report and state.evaluation_report.advice:
        return state.evaluation_report.advice
    if state.summary_evaluation and state.summary_evaluation.advice:
        return state.summary_evaluation.advice
    return ""


def _key_events(state: BattlePlannerState) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if state.evaluation_report is not None:
        events.extend(state.evaluation_report.diagnostic_events)

    runner_report = _runner_report_payload(state)
    for event in _as_list(runner_report.get("battlefield_events"))[:20]:
        event_payload = _as_dict(event)
        if event_payload:
            events.append({"event": "battlefield_event", **event_payload})
    return events


def _runner_report_payload(state: BattlePlannerState) -> dict[str, Any]:
    if state.simulation_result is None:
        return {}
    return _as_dict(state.simulation_result.raw_summary.get("runner_report"))


def _summary_excerpt(summary_md: str, *, max_lines: int = 8, max_chars: int = 1200) -> str:
    lines = [line for line in summary_md.splitlines() if line.strip()]
    excerpt = "\n".join(lines[:max_lines])
    return excerpt[:max_chars]


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
