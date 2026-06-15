from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SimulationRunResult(BaseModel):
    """单次仿真运行结果。"""

    steps: int = Field(description="仿真执行的决策步数。")
    done: bool = Field(description="仿真环境是否进入终止或截断状态。")
    logs: list[str] = Field(default_factory=list, description="仿真运行日志摘要。")
    raw_summary: dict[str, Any] = Field(default_factory=dict, description="仿真原始报告摘要。")
    metrics: dict[str, float | int | str | bool | dict[str, Any]] = Field(
        default_factory=dict, description="单局可观测指标。"
    )


class EvaluationFindingSpec(BaseModel):
    """单次仿真的评估发现。"""

    code: str = Field(description="发现编码。")
    message: str = Field(default="", description="发现说明。")
    severity: Literal["info", "warning", "error"] = Field(default="warning", description="严重级别。")
    detail: dict[str, Any] = Field(default_factory=dict, description="补充信息。")


class EvaluationReport(BaseModel):
    """单次仿真结果的评估判定。"""

    objective_achieved: bool = Field(default=False, description="本次仿真是否达成业务目标。")
    findings: list[EvaluationFindingSpec] = Field(default_factory=list, description="评估发现。")
    meta: dict[str, Any] = Field(default_factory=dict, description="预留扩展字段。")
