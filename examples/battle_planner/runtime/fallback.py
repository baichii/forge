from __future__ import annotations

from typing import Any

from battle_planner.data.demo_models import PlannedAgentParams

from forge.utils.specs import TickAgentSpec


def fallback_markdown(title: str, body: str) -> str:
    return f"# {title}\n\n{body}\n"


DEFAULT_TICK_AGENT_PARAMS: dict[str, dict[str, Any]] = {
    "air_to_sea_strike_agent": {
        "start_time": 120,
        "end_time": 600,
        "unit_ids": ["blue_F/A-18F型“超级大黄蜂”战斗机_14"],
        "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
        "wp_num": 2,
        "clear_targets": True,
    },
    "naval_to_sea_strike_agent": {
        "start_time": 180,
        "end_time": 600,
        "unit_ids": ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_2"],
        "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
        "wp_num": 2,
        "clear_targets": True,
    },
}


def fallback_agent_params(agent_specs: list[TickAgentSpec]) -> list[PlannedAgentParams]:
    planned: list[PlannedAgentParams] = []
    for spec in agent_specs:
        params: dict[str, Any] = {
            param.name: param.default_value
            for param in spec.params.values()
            if param.default_value is not None
        }
        params.update(DEFAULT_TICK_AGENT_PARAMS.get(spec.name, {}))
        planned.append(
            PlannedAgentParams(
                agent_name=spec.name,
                params=params,
                rationale="LLM 不可用或输出无法解析，使用 tick agent 默认参数。",
            )
        )
    return planned
