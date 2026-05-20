from __future__ import annotations

import contextlib
import copy
import importlib
import io
from typing import Any


def load_zc_lite_scenario() -> dict[str, Any]:
    """Load scenario_zc_lite while suppressing its import-time pprint."""
    with contextlib.redirect_stdout(io.StringIO()):
        module = importlib.import_module("scenario.scenario_zc_lite")
    return copy.deepcopy(module.scenario_conf)


def summarize_scenario(scenario_conf: dict[str, Any]) -> dict[str, Any]:
    units = scenario_conf.get("units", {})
    side_summaries: dict[str, Any] = {}
    for side_name, side_units in units.items():
        unit_count = len(side_units)
        aircraft_count = sum(len(unit.get("aircrafts", [])) for unit in side_units)
        weapon_count = sum(len(unit.get("weapons", [])) for unit in side_units)
        side_summaries[side_name] = {
            "unit_count": unit_count,
            "aircraft_group_count": aircraft_count,
            "weapon_group_count": weapon_count,
            "sample_units": [
                {
                    "name": unit.get("name"),
                    "prototype": unit.get("prototype"),
                    "position": unit.get("position"),
                }
                for unit in side_units[:3]
            ],
        }

    return {
        "name": scenario_conf.get("name"),
        "description": scenario_conf.get("description"),
        "start_time": scenario_conf.get("start_time"),
        "end_time": scenario_conf.get("end_time"),
        "tick_time": scenario_conf.get("tick_time"),
        "relationship": scenario_conf.get("relationship", {}),
        "sides": side_summaries,
    }


def render_scenario_summary_md(summary: dict[str, Any]) -> str:
    lines = [
        f"# 想定摘要：{summary.get('name')}",
        "",
        f"- 描述：{summary.get('description')}",
        f"- 时间：{summary.get('start_time')} 至 {summary.get('end_time')}",
        f"- tick：{summary.get('tick_time')}",
        "",
        "## 阵营与兵力",
    ]
    for side_name, side_summary in summary.get("sides", {}).items():
        lines.extend(
            [
                f"### {side_name}",
                f"- 单位组数量：{side_summary['unit_count']}",
                f"- 航空编组数量：{side_summary['aircraft_group_count']}",
                f"- 武器编组数量：{side_summary['weapon_group_count']}",
            ]
        )
        for unit in side_summary["sample_units"]:
            lines.append(f"- {unit['name']}：{unit['prototype']}，位置 {unit['position']}")
    return "\n".join(lines)
