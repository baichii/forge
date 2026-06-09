from __future__ import annotations

from typing import Any

from battle_planner.model import EvaluationReport, SimulationRunResult


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
            damage=damage, initial_health=initial_health, target_count=target_count
        )

        requested_weapon_count, weapon_events = _collect_requested_weapon_count(agent_reports)
        action_count = sum(int(_as_dict(agent).get("action_count") or 0) for agent in agent_reports)
        inactive_agents = [
            str(_as_dict(agent).get("agent_instance_id") or "")
            for agent in agent_reports
            if int(_as_dict(agent).get("action_count") or 0) <= 0
        ]
        inactive_agents = [item for item in inactive_agents if item]

        hard_violations = _build_hard_violations(
            result=result,
            target_count=target_count,
            action_count=action_count,
        )
        score = _score(
            objective_achieved=objective_achieved,
            damage_ratio=damage_ratio,
            requested_weapon_count=requested_weapon_count,
            inactive_agent_count=len(inactive_agents),
        )

        return EvaluationReport(
            score=score,
            hard_violations=hard_violations,
            mission_metrics={
                "sim_decision_steps": result.steps,
                "env_done": result.done,
                "objective_achieved": objective_achieved,
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
            },
            diagnostic_events=[
                {
                    "event": "target_outcome",
                    "objective_achieved": objective_achieved,
                    "targets": target_stats,
                },
                {
                    "event": "weapon_request",
                    "requested_weapon_count": requested_weapon_count,
                    "detail": "基于 runner 下发 action 中的 wp_num/wp_nums/weapon_nums 估算请求火力。",
                    "actions": weapon_events,
                },
                {
                    "event": "score_rule",
                    "detail": "目标摧毁优先；未摧毁时按毁伤比例计分；目标摧毁后对请求火力数做轻量扣分。",
                },
            ],
            advice=_build_advice(
                objective_achieved=objective_achieved,
                damage=damage,
                requested_weapon_count=requested_weapon_count,
                inactive_agents=inactive_agents,
                hard_violations=hard_violations,
            ),
        )


def _collect_target_statistic_results(runner_report: dict[str, Any]) -> dict[str, Any]:
    callbacks = _as_dict(runner_report.get("callbacks"))
    results: dict[str, Any] = {}
    for callback_payload in callbacks.values():
        callback_result = _as_dict(callback_payload)
        if not callback_result:
            continue
        if not all(_looks_like_target_statistic(_as_dict(item)) for item in callback_result.values()):
            continue
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


def _build_hard_violations(
    *,
    result: SimulationRunResult,
    target_count: int,
    action_count: int,
) -> list[str]:
    hard_violations: list[str] = []
    if result.steps <= 0:
        hard_violations.append("simulation produced no steps")
    if target_count <= 0:
        hard_violations.append("target_statistic callback produced no target result")
    if action_count <= 0:
        hard_violations.append("no agent action was dispatched")
    return hard_violations


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


def _build_advice(
    *,
    objective_achieved: bool,
    damage: float,
    requested_weapon_count: int,
    inactive_agents: list[str],
    hard_violations: list[str],
) -> str:
    if "target_statistic callback produced no target result" in hard_violations:
        return "未获取到目标统计结果，优先检查 callback 配置和目标 id。"
    if "no agent action was dispatched" in hard_violations:
        return "未下发任何 agent 动作，优先检查时间窗口、目标接地和单位匹配。"
    if objective_achieved:
        return f"目标已摧毁，本轮请求火力数为 {requested_weapon_count}；下一轮可降低火力寻找临界条件。"
    if inactive_agents:
        return "目标未摧毁且存在未执行 agent，下一轮优先检查未执行 agent 的时间窗口和单位/目标匹配。"
    if damage > 0:
        return f"目标未摧毁但已造成 {round(damage, 4)} 点毁伤，下一轮可增强火力或调整打击时序。"
    return "目标未摧毁且未形成可见毁伤，下一轮优先检查武器能力、射程、命中窗口和任务格式。"


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
