from __future__ import annotations

import copy
from typing import Any

from battle_planner.keys import CONT

from forge.core.lib.callback import CallBack
from forge.core.specs import CallbackParams


class StepMetricCallback(CallBack):
    """Minimal runtime metric callback for runner smoke validation."""

    def __init__(self, params: CallbackParams):
        super().__init__(params=params)
        self.run_begin_count = 0
        self.run_end_count = 0
        self.step_begin_count = 0
        self.step_end_count = 0

    def on_begin(self) -> None:
        self.run_begin_count += 1

    def on_end(self) -> None:
        self.run_end_count += 1

    def on_step_begin(self) -> None:
        self.step_begin_count += 1

    def on_step_end(self) -> None:
        self.step_end_count += 1

    def result(self) -> dict[str, Any]:
        return {
            "run_begin_count": self.run_begin_count,
            "run_end_count": self.run_end_count,
            "step_begin_count": self.step_begin_count,
            "step_end_count": self.step_end_count,
        }


class TargetStatistic(CallBack):
    """单位信息统计

    fixme:
        这是一个很粗糙的单位能力获取，很多特性和容错并未考虑

    """

    def __init__(self, params: CallbackParams):
        super().__init__(params=params)
        self._side = self.params["side"]
        self._target_ids = self.params["target_ids"]
        self._target_init_snapshots = {}
        self._target_last_snapshots = {}

    def on_step_begin(self):
        target_state = self._target_state()
        if not target_state:
            return

        # fixme: 性能优化
        for target_id in self._target_ids:
            if target_id in self._target_init_snapshots:
                continue
            snapshot = target_state.get(target_id)
            if snapshot is not None:
                self._target_init_snapshots[target_id] = copy.deepcopy(snapshot)

    def on_end(self):
        target_state = self._target_state()
        if not target_state:
            return

        for target_id in self._target_ids:
            snapshot = target_state.get(target_id)
            if snapshot is not None:
                self._target_last_snapshots[target_id] = copy.deepcopy(snapshot)

    def result(self):
        results = {}
        for target_id in self._target_ids:
            initial_snapshot = self._target_init_snapshots.get(target_id)
            current_snapshot = self._target_last_snapshots.get(target_id)
            alive = current_snapshot is not None

            initial = self._build_snapshot_summary(initial_snapshot)
            current = self._build_snapshot_summary(current_snapshot, alive=alive, initial=initial)

            results[target_id] = {
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
        return results

    def _target_state(self) -> dict[str, Any]:
        last_observation = getattr(self._runner, "_last_observation", {})
        if not isinstance(last_observation, dict):
            return {}

        cont_observation = last_observation.get(CONT, {})
        if not isinstance(cont_observation, dict):
            return {}

        state = cont_observation.get("state", {})
        if not isinstance(state, dict):
            return {}

        target_state = state.get(self._side, {})
        return target_state if isinstance(target_state, dict) else {}

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
