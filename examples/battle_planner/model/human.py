from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskStyle = Literal["aggressive", "balanced", "conservative"]


class PlanHumanInputSpec(BaseModel):
    """任务方案层人工输入。"""

    goal: str = Field(default="", description="优化目标。")
    risk_style: RiskStyle = Field(default="balanced", description="风险偏好。")
    constraints: list[str] = Field(default_factory=list, description="约束配置。")
    risk_points: list[str] = Field(default_factory=list, description="风险点。")
    notes: str = Field(default="", description="业务备注。")


class BranchHumanInputSpec(BaseModel):
    """任务分支层人工输入。"""

    goal: str = Field(default="", description="分支优化目标。")
    risk_style: RiskStyle = Field(default="balanced", description="风险偏好。")
    constraints: list[str] = Field(default_factory=list, description="约束配置。")
    risk_points: list[str] = Field(default_factory=list, description="风险点。")
    notes: str = Field(default="", description="业务备注。")
