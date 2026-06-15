from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from battle_planner.model import EvaluationAggregateSpec, SimulationRunResult
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.resource import load_callback_specs

from forge.core.specs import ParamSpecTemplate


def result_evaluation_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.RESULT_EVALUATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
    )
    simulation_results = list(state.simulation_results)
    if not simulation_results and state.simulation_result is not None:
        simulation_results = [state.simulation_result]
    if not simulation_results:
        state.mark_error("evaluation requires simulation_results")
        event_handler(
            EventTypes.LOG,
            node=node_name,
            phase=EventPhases.ERROR,
            level=EventLevels.NODE,
            iteration_index=state.iteration_index,
            payload={"error": state.error or "missing simulation_results"},
        )
        return state
    state.simulation_results = simulation_results
    state.evaluation_reports = []
    state.evaluation_report = None
    state.evaluation_summary = _build_metric_summary(simulation_results)
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "run_count": len(simulation_results),
            "metric_count": len(state.evaluation_summary.metric_summary) if state.evaluation_summary else 0,
        },
    )
    return state


def _build_metric_summary(simulation_results: list[SimulationRunResult]) -> EvaluationAggregateSpec:
    for result in simulation_results:
        result.metrics.update(_collect_callback_metrics(_collect_callback_reports(result)))

    return EvaluationAggregateSpec(
        case_count=len(simulation_results),
        metric_summary=_aggregate_declared_metrics(simulation_results),
    )


def _collect_callback_reports(result: SimulationRunResult) -> dict[str, Any]:
    runner_report = _as_dict(result.raw_summary.get("runner_report"))
    return _as_dict(runner_report.get("callbacks"))


def _collect_callback_metrics(callback_reports: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for callback_payload in callback_reports.values():
        callback_metrics = _as_dict(_as_dict(callback_payload).get("metrics"))
        metrics.update(callback_metrics)
    return metrics


def _aggregate_declared_metrics(simulation_results: list[SimulationRunResult]) -> dict[str, Any]:
    declarations = _load_metric_declarations()
    metric_values: dict[str, list[float]] = {}
    for result in simulation_results:
        for key, value in result.metrics.items():
            declaration = declarations.get(key)
            if declaration is None or declaration.other.get("agg") is not True:
                continue
            samples = _metric_samples(value)
            if samples:
                metric_values.setdefault(key, []).extend(samples)

    return {
        key: {
            "key": key,
            "name": declarations[key].name,
            "description": declarations[key].description,
            "mean": _round_metric(mean(values)),
            "min": _round_metric(min(values)),
            "max": _round_metric(max(values)),
            "std": _round_metric(pstdev(values) if len(values) > 1 else 0.0),
        }
        for key, values in metric_values.items()
        if values
    }


def _load_metric_declarations() -> dict[str, ParamSpecTemplate]:
    declarations: dict[str, ParamSpecTemplate] = {}
    for callback_spec in load_callback_specs():
        declarations.update(callback_spec.metrics)
    return declarations


def _metric_samples(value: Any) -> list[float]:
    if isinstance(value, bool):
        return []
    if isinstance(value, int | float):
        return [float(value)]
    if isinstance(value, dict):
        return [
            float(item)
            for item in value.values()
            if isinstance(item, int | float) and not isinstance(item, bool)
        ]
    return []


def _round_metric(value: float) -> int | float:
    rounded = round(value, 4)
    return int(rounded) if rounded.is_integer() else rounded


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
