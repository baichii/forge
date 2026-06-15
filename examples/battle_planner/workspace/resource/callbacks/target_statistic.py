from __future__ import annotations

import copy
from typing import Any

from battle_planner.keys import CONT

from forge.core.lib.callback import CallBack
from forge.core.specs import CallbackParams, CallbackSpec, ParamSpec, ParamSpecTemplate, ParamType

ENTRYPOINT = "TargetStatistic"

TARGET_STATISTIC_DECLARATION = CallbackSpec(
    name="target_statistic",
    description="统计指定目标在仿真开始和结束时的状态变化，并给出目标摧毁类任务的完成情况。",
    version="0.1.0",
    entrypoint=ENTRYPOINT,
    params={
        "side": ParamSpec.side.redeclaration(
            required=True,
            description="从该阵营的态势中读取目标单位状态。",
        ),
        "target_ids": ParamSpec.target_ids.redeclaration(
            type=ParamType.LIST,
            description="需要跟踪和评估的目标单位唯一 ID。",
        ),
    },
    metrics={
        "target_count": ParamSpecTemplate(
            name="目标数量",
            description="本次 callback 评估的目标单位数量。",
            type=ParamType.INT,
            other={"agg": True},
        ),
        "target_destroyed_count": ParamSpecTemplate(
            name="目标摧毁数量",
            description="终局态势中已经不存在或判定为不存活的目标数量。",
            type=ParamType.INT,
            other={"agg": True},
        ),
        "target_damage_ratio": ParamSpecTemplate(
            name="目标毁伤比例",
            description="每个目标单位的毁伤比例。",
            type=ParamType.DICT,
            other={"agg": True},
        ),
    },
)


class TargetStatistic(CallBack):
    """单位信息统计

    fixme:
        这是一个很粗糙的单位能力获取，很多特性和容错并未考虑

    """

    declaration = TARGET_STATISTIC_DECLARATION

    def __init__(self, params: CallbackParams):
        super().__init__(params=params)
        self._side = self.params["side"]
        self._target_ids = self.params["target_ids"]
        self._target_init_snapshots = {}
        self._target_last_snapshots = {}

    def observe(self, observation: dict[str, Any]):
        target_state = self._target_state(observation)
        if not target_state:
            return

        for target_id in self._target_ids:
            if target_id in self._target_init_snapshots:
                continue
            snapshot = target_state.get(target_id)
            if snapshot is not None:
                self._target_init_snapshots[target_id] = copy.deepcopy(snapshot)

        for target_id in self._target_ids:
            snapshot = target_state.get(target_id)
            if snapshot is not None:
                self._target_last_snapshots[target_id] = copy.deepcopy(snapshot)

    def result(self):
        targets = {}
        for target_id in self._target_ids:
            initial_snapshot = self._target_init_snapshots.get(target_id)
            current_snapshot = self._target_last_snapshots.get(target_id)
            alive = current_snapshot is not None

            initial = self._build_snapshot_summary(initial_snapshot)
            current = self._build_snapshot_summary(current_snapshot, alive=alive, initial=initial)

            targets[target_id] = {
                "alive": alive,
                "initial": initial,
                "current": current,
                "delta": {
                    "health": self._delta_number(initial["health"], current["health"]),
                    "health_percent": self._delta_number(
                        initial["health_percent"],
                        current["health_percent"],
                        digits=4,
                    ),
                    "ammo_count": self._delta_number(
                        initial["ammo_count"],
                        current["ammo_count"],
                    ),
                },
            }

        target_count = len(targets)
        destroyed_count = sum(1 for item in targets.values() if not item["alive"])
        damage_ratio_by_target = self._damage_ratio_by_target(
            targets=targets,
        )

        return {
            "schema_version": "callback_eval.v0",
            "callback_instance_id": self.id,
            "callback_name": self.name,
            "metrics": {
                "target_count": target_count,
                "target_destroyed_count": destroyed_count,
                "target_damage_ratio": damage_ratio_by_target,
            },
            "payload": {"targets": targets},
        }

    def _target_state(self, observation: dict[str, Any]) -> dict[str, Any]:
        cont_observation = observation.get(CONT, {})
        if not isinstance(cont_observation, dict):
            return {}

        state = cont_observation.get("state", {})
        if not isinstance(state, dict):
            return {}

        target_state = state.get(self._side, {})
        return target_state if isinstance(target_state, dict) else {}

    def _damage_ratio_by_target(
        self,
        *,
        targets: dict[str, Any],
    ) -> dict[str, int | float]:
        result = {}
        for target_id, target_payload in targets.items():
            initial = target_payload.get("initial", {})
            delta = target_payload.get("delta", {})
            initial_health = number_or_zero(initial.get("health"))
            health_delta = number_or_zero(delta.get("health"))
            damage = max(0.0, -health_delta)
            damage_ratio = min(1.0, damage / initial_health) if initial_health > 0 else 0.0
            result[target_id] = round_metric(damage_ratio)
        return result

    def _build_snapshot_summary(
        self,
        snapshot: dict[str, Any] | None,
        *,
        alive: bool = True,
        initial: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if snapshot is None:
            return {
                "health": self._round_number(0.0)
                if not alive and initial and initial["health"] is not None
                else None,
                "health_percent": (
                    self._round_number(0.0, digits=4)
                    if not alive and initial and initial["health_percent"] is not None
                    else None
                ),
                "ammo_count": self._round_number(0.0)
                if not alive and initial and initial["ammo_count"] is not None
                else None,
            }

        return {
            "health": self._round_number(snapshot.get("health")),
            "health_percent": self._round_number(snapshot.get("health_percent"), digits=4),
            "ammo_count": self._ammo_count(snapshot.get("weapons", {})),
        }

    @staticmethod
    def _ammo_count(weapons: Any) -> int | float | None:
        if not isinstance(weapons, dict):
            return None

        count = 0
        for weapon in weapons.values():
            if isinstance(weapon, dict):
                count += weapon.get("num", 0)
        return count

    @staticmethod
    def _delta_number(
        initial_value: int | float | None,
        current_value: int | float | None,
        *,
        digits: int | None = None,
    ) -> int | float | None:
        if initial_value is None or current_value is None:
            return None
        return TargetStatistic._round_number(current_value - initial_value, digits=digits)

    @staticmethod
    def _round_number(value: Any, *, digits: int | None = None) -> int | float | None:
        if not isinstance(value, int | float):
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        rounded_value = round(value, 4 if digits is None else digits)
        return int(rounded_value) if rounded_value.is_integer() else rounded_value


def number_or_zero(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    return float(value) if isinstance(value, int | float) else 0.0


def round_metric(value: float) -> int | float:
    rounded = round(value, 4)
    return int(rounded) if rounded.is_integer() else rounded
