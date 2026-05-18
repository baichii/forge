from __future__ import annotations

from typing import Any


def describe_demo_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "query_units",
            "description": "从想定摘要中查询指定阵营的单位概览。首版是静态摘要工具。",
            "args": {"side": "red|blue"},
        },
        {
            "name": "query_attack_candidates",
            "description": "查询可执行固定目标打击的候选单位。首版返回预置 F/A-18F 编组。",
            "args": {"target_id": "目标 id", "side": "blue"},
        },
        {
            "name": "can_attack",
            "description": "判断指定单位是否可以攻击指定目标。首版只做 demo 占位判断。",
            "args": {"unit_id": "单位 id", "target_id": "目标 id"},
        },
    ]
