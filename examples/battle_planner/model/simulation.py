from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SimulationRunResult(BaseModel):
    """单次仿真运行结果。"""

    steps: int = Field(description="仿真执行的决策步数。")
    done: bool = Field(description="仿真环境是否进入终止或截断状态。")
    logs: list[str] = Field(default_factory=list, description="仿真运行日志摘要。")
    raw_summary: dict[str, Any] = Field(default_factory=dict, description="仿真原始报告摘要。")


class EvaluationReport(BaseModel):
    """单次仿真结果的评估报告。"""

    score: float = Field(description="本次仿真的综合评分。")
    hard_violations: list[str] = Field(default_factory=list, description="硬性约束违规项。")
    mission_metrics: dict[str, float | int | str | bool] = Field(
        default_factory=dict,
        description="任务评估指标。",
    )
    diagnostic_events: list[dict[str, Any]] = Field(default_factory=list, description="诊断事件。")
    advice: str = Field(default="", description="面向下一轮迭代的建议。")
