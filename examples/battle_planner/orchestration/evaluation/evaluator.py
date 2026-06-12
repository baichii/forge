from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any

from battle_planner.model import (
    EvaluationAggregateSpec,
    EvaluationFailureReason,
    EvaluationFindingSpec,
    EvaluationReport,
    SimulationRunResult,
)


class TargetOutcomeEvaluator:
    """Evaluate one simulation run from runner report facts."""

    def evaluate(self, result: SimulationRunResult) -> EvaluationReport:
        runner_report = _as_dict(result.raw_summary.get("runner_report"))
        target_results = _collect_target_statistic_results(runner_report)
        agent_reports = _as_list(runner_report.get("agents"))

        target_stats = [
            _target_metric(target_id, _as_dict(payload)) for target_id, payload in target_results.items()
        ]
        target_count = len(target_stats)
        destroyed_count = sum(1 for item in target_stats if item["destroyed"])
        objective_achieved = target_count > 0 and destroyed_count == target_count

        initial_health = _sum_numbers(item["initial_health"] for item in target_stats)
        current_health = _sum_numbers(item["current_health"] for item in target_stats)
        health_delta = _sum_numbers(item["health_delta"] for item in target_stats)
        damage = max(0.0, -health_delta)
        damage_ratio = _damage_ratio(
            damage=damage,
            initial_health=initial_health,
            target_count=target_count,
        )

        requested_weapon_count, _weapon_events = _collect_requested_weapon_count(agent_reports)
        action_count = sum(int(_as_dict(agent).get("action_count") or 0) for agent in agent_reports)
        inactive_agents = [
            str(_as_dict(agent).get("agent_instance_id") or "")
            for agent in agent_reports
            if int(_as_dict(agent).get("action_count") or 0) <= 0
        ]
        inactive_agents = [item for item in inactive_agents if item]

        result.metrics.update(
            {
                "sim_decision_steps": result.steps,
                "env_done": result.done,
                "target_count": target_count,
                "target_destroyed_count": destroyed_count,
                "target_initial_health": _round_metric(initial_health),
                "target_current_health": _round_metric(current_health),
                "target_health_delta": _round_metric(health_delta),
                "target_damage": _round_metric(damage),
                "target_damage_ratio": _round_metric(damage_ratio),
                "agent_action_count": action_count,
                "inactive_agent_count": len(inactive_agents),
                "requested_weapon_count": requested_weapon_count,
            }
        )

        return EvaluationReport(
            objective_achieved=objective_achieved,
            findings=_build_findings(
                result=result,
                target_count=target_count,
                action_count=action_count,
                objective_achieved=objective_achieved,
                inactive_agents=inactive_agents,
            ),
        )


def aggregate_evaluation_reports(
    reports: list[EvaluationReport],
    simulation_results: list[SimulationRunResult] | None = None,
) -> EvaluationAggregateSpec:
    """聚合同一 DeductionSpec 下的多次仿真评估结果。"""

    if not reports:
        return EvaluationAggregateSpec()

    simulation_results = simulation_results or []
    scores = [
        _score_from_metrics(
            report=report,
            metrics=simulation_results[index].metrics if index < len(simulation_results) else {},
        )
        for index, report in enumerate(reports)
    ]
    success_count = sum(
        1 for report in reports if report.objective_achieved and not _has_error_findings(report)
    )
    best_index, _ = max(enumerate(scores), key=lambda item: item[1])
    return EvaluationAggregateSpec(
        case_count=len(reports),
        success_count=success_count,
        success_rate=_round_metric(success_count / len(reports)),
        mean_score=_round_metric(mean(scores)),
        best_score=_round_metric(max(scores)),
        worst_score=_round_metric(min(scores)),
        std_score=_round_metric(pstdev(scores) if len(scores) > 1 else 0.0),
        objective_achieved_count=sum(1 for report in reports if report.objective_achieved),
        recommended_simulation_index=best_index,
        failure_reasons=_aggregate_failure_reasons(reports),
        metric_summary=_aggregate_numeric_metrics(simulation_results),
    )


def _build_findings(
    *,
    result: SimulationRunResult,
    target_count: int,
    action_count: int,
    objective_achieved: bool,
    inactive_agents: list[str],
) -> list[EvaluationFindingSpec]:
    findings: list[EvaluationFindingSpec] = []
    if result.steps <= 0:
        findings.append(
            EvaluationFindingSpec(
                code="simulation_no_steps",
                message="仿真没有产生决策步。",
                severity="error",
            )
        )
    if target_count <= 0:
        findings.append(
            EvaluationFindingSpec(
                code="target_callback_missing",
                message="未获取到目标统计 callback 结果。",
                severity="error",
            )
        )
    if action_count <= 0:
        findings.append(
            EvaluationFindingSpec(
                code="agent_no_action_dispatched",
                message="未下发任何 agent 动作。",
                severity="error",
            )
        )
    if target_count > 0 and not objective_achieved:
        findings.append(
            EvaluationFindingSpec(
                code="target_not_destroyed",
                message="目标未全部摧毁。",
                severity="warning",
            )
        )
    if inactive_agents:
        findings.append(
            EvaluationFindingSpec(
                code="agent_inactive",
                message="存在未执行动作的 agent。",
                severity="warning",
                detail={"agent_instance_ids": inactive_agents},
            )
        )
    return findings


def _score_from_metrics(*, report: EvaluationReport, metrics: dict[str, Any]) -> float:
    return _score(
        objective_achieved=report.objective_achieved,
        damage_ratio=_number_or_zero(metrics.get("target_damage_ratio")),
        requested_weapon_count=int(_number_or_zero(metrics.get("requested_weapon_count"))),
        inactive_agent_count=int(_number_or_zero(metrics.get("inactive_agent_count"))),
    )


def _has_error_findings(report: EvaluationReport) -> bool:
    return any(finding.severity == "error" for finding in report.findings)


def _aggregate_failure_reasons(reports: list[EvaluationReport]) -> list[EvaluationFailureReason]:
    counter: Counter[str] = Counter()
    summaries: dict[str, str] = {}
    for report in reports:
        for finding in report.findings:
            if report.objective_achieved and finding.severity != "error":
                continue
            counter.update([finding.code])
            summaries.setdefault(finding.code, finding.message or finding.code)
    return [
        EvaluationFailureReason(reason=reason, count=count, summary=summaries.get(reason, reason))
        for reason, count in counter.most_common()
    ]


def _aggregate_numeric_metrics(simulation_results: list[SimulationRunResult]) -> dict[str, Any]:
    metric_values: dict[str, list[float]] = {}
    for result in simulation_results:
        for key, value in result.metrics.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, int | float):
                metric_values.setdefault(key, []).append(float(value))

    return {
        key: {
            "mean": _round_metric(mean(values)),
            "min": _round_metric(min(values)),
            "max": _round_metric(max(values)),
            "std": _round_metric(pstdev(values) if len(values) > 1 else 0.0),
        }
        for key, values in metric_values.items()
        if values
    }


def _collect_target_statistic_results(runner_report: dict[str, Any]) -> dict[str, Any]:
    callbacks = _as_dict(runner_report.get("callbacks"))
    results: dict[str, Any] = {}
    for callback_payload in callbacks.values():
        callback_result = _as_dict(callback_payload)
        if not callback_result:
            continue
        targets = _as_dict(_as_dict(callback_result.get("payload")).get("targets"))
        if targets:
            results.update(targets)
            continue
        if all(_looks_like_target_statistic(_as_dict(item)) for item in callback_result.values()):
            results.update(callback_result)
    return results


def _looks_like_target_statistic(payload: dict[str, Any]) -> bool:
    return {"alive", "initial", "current", "delta"}.issubset(payload.keys())


def _target_metric(target_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    initial = _as_dict(payload.get("initial"))
    current = _as_dict(payload.get("current"))
    delta = _as_dict(payload.get("delta"))
    alive = bool(payload.get("alive", True))
    return {
        "target_id": target_id,
        "alive": alive,
        "destroyed": not alive,
        "initial_health": _number_or_zero(initial.get("health")),
        "current_health": _number_or_zero(current.get("health")),
        "health_delta": _number_or_zero(delta.get("health")),
        "health_percent_delta": _number_or_zero(delta.get("health_percent")),
    }


def _collect_requested_weapon_count(agent_reports: list[Any]) -> tuple[int, list[dict[str, Any]]]:
    total = 0
    weapon_events: list[dict[str, Any]] = []
    for agent in agent_reports:
        agent_payload = _as_dict(agent)
        for event in _as_list(agent_payload.get("events")):
            event_payload = _as_dict(event)
            for action in _as_list(event_payload.get("raw_actions")):
                count = _weapon_count_from_action(_as_dict(action))
                if count <= 0:
                    continue
                total += count
                weapon_events.append(
                    {
                        "agent_instance_id": agent_payload.get("agent_instance_id"),
                        "agent_name": agent_payload.get("agent_name"),
                        "step": event_payload.get("step"),
                        "sim_time": event_payload.get("sim_time"),
                        "requested_weapon_count": count,
                    }
                )
    return total, weapon_events


def _weapon_count_from_action(action: dict[str, Any]) -> int:
    action_params = _as_dict(action.get("params"))
    mission_params = _as_dict(action_params.get("params"))
    unit_ids = _as_list(mission_params.get("unit_ids"))
    unit_count = max(1, len(unit_ids))

    if isinstance(mission_params.get("wp_nums"), list):
        return _sum_ints(mission_params["wp_nums"])
    if isinstance(mission_params.get("weapon_nums"), list):
        return _sum_ints(mission_params["weapon_nums"])

    wp_num = mission_params.get("wp_num")
    if isinstance(wp_num, int | float) and not isinstance(wp_num, bool):
        return max(0, int(wp_num)) * unit_count
    return 0


def _score(
    *,
    objective_achieved: bool,
    damage_ratio: float,
    requested_weapon_count: int,
    inactive_agent_count: int,
) -> float:
    if objective_achieved:
        weapon_penalty = min(20.0, requested_weapon_count * 0.5)
        inactive_penalty = min(20.0, inactive_agent_count * 10.0)
        return round(max(0.0, 100.0 - weapon_penalty - inactive_penalty), 2)
    inactive_penalty = min(20.0, inactive_agent_count * 10.0)
    return round(max(0.0, damage_ratio * 80.0 - inactive_penalty), 2)


def _damage_ratio(*, damage: float, initial_health: float, target_count: int) -> float:
    if initial_health > 0:
        return min(1.0, max(0.0, damage / initial_health))
    return 0.0 if target_count <= 0 else 1.0


def _sum_numbers(values: Any) -> float:
    total = 0.0
    for value in values:
        if isinstance(value, int | float) and not isinstance(value, bool):
            total += float(value)
    return total


def _sum_ints(values: list[Any]) -> int:
    total = 0
    for value in values:
        if isinstance(value, int | float) and not isinstance(value, bool):
            total += max(0, int(value))
    return total


def _number_or_zero(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    return float(value) if isinstance(value, int | float) else 0.0


def _round_metric(value: float) -> int | float:
    rounded = round(value, 4)
    return int(rounded) if rounded.is_integer() else rounded


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
