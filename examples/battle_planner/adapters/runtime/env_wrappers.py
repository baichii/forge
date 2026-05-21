from __future__ import annotations

from typing import Any

from battle_planner.adapters.runtime.specs import BattlefieldEvent


class PysimInfoWrapper:
    """Normalize pysim runtime info for the battle-planner runner."""

    def __init__(self, env: Any):
        self.env = env
        self._step = 0

    def reset(self, *args: Any, **kwargs: Any) -> Any:
        self._step = 0
        observation, info = self.env.reset(*args, **kwargs)
        return self._normalize_observation(observation), info

    def step(self, action: Any) -> tuple[Any, Any, bool, bool, dict[str, Any]]:
        self._step += 1
        observation, reward, terminated, truncated, info = self.env.step(action)
        normalized_observation = self._normalize_observation(observation)
        normalized_info = self._normalize_info(info, normalized_observation)
        return normalized_observation, reward, terminated, truncated, normalized_info

    def close(self) -> Any:
        return self.env.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.env, name)

    def _normalize_info(self, info: dict[str, Any], observation: Any) -> dict[str, Any]:
        normalized_info = dict(info) if isinstance(info, dict) else {}
        normalized_info["battlefield_events"] = self._collect_battlefield_events(
            normalized_info,
            observation.get("sim_time") if isinstance(observation, dict) else None,
        )
        return normalized_info

    def _normalize_observation(self, observation: Any) -> Any:
        if not isinstance(observation, dict):
            return observation
        normalized_observation = dict(observation)
        sim_time = self._extract_sim_time(observation)
        if sim_time is not None:
            normalized_observation["sim_time"] = sim_time
        return normalized_observation

    def _collect_battlefield_events(
        self,
        info: dict[str, Any],
        sim_time: float | None,
    ) -> list[BattlefieldEvent]:
        damage_info = info.get("damage")
        if not damage_info:
            return []

        events: list[BattlefieldEvent] = []
        for side, side_damage in damage_info.items():
            for unit_id, unit_events in side_damage.items():
                for unit_event in unit_events:
                    damage_reason = self._enum_name("DestroyReason", unit_event.get("damage_reason"))
                    unit_type = self._enum_name("UnitType", unit_event.get("type"))
                    events.append(
                        BattlefieldEvent(
                            step=self._step,
                            sim_time=sim_time,
                            event_type="unit_destroyed" if damage_reason == "Attacked" else "unit_damage",
                            side=str(side),
                            unit_id=str(unit_id),
                            info={
                                "damage_reason": damage_reason,
                                "damage_point": unit_event.get("damage_point"),
                                "unit_type": unit_type,
                                "unit_subtype": unit_event.get("subtype"),
                            },
                        )
                    )
        return events

    def _extract_sim_time(self, observation: Any) -> float | None:
        if not isinstance(observation, dict):
            return None
        sim_time = observation.get("sim_time", observation.get("time"))
        if sim_time is None:
            sim_time = getattr(self.env, "sim_time", None)
        return float(sim_time) if sim_time is not None else None

    def _enum_name(self, enum_name: str, value: Any) -> str | int | None:
        if value is None:
            return None
        if hasattr(value, "name"):
            return value.name
        try:
            from pysim.schema import enums

            enum_cls = getattr(enums, enum_name)
            return enum_cls(value).name
        except Exception:
            return value
