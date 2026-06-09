"""外部或本地来源的任务资源模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TickAgentSourceSpec(BaseModel):
    """tick agent 展示信息。"""

    tick_agent_id: str = Field(description="tick agent 唯一标识，全局唯一。")
    name: str = Field(description="tick agent 名称。")
    description: str = Field(default="", description="tick agent 描述。")
    params: dict[str, object] = Field(default_factory=dict, description="tick agent 参数声明。")
    version: str = Field(default="", description="tick agent 版本。")


class TaskBranchSpec(BaseModel):
    """任务方案中的分支卡片。"""

    branch_id: int = Field(description="分支 ID，在所属任务方案内从 1 开始自增。")
    name: str = Field(description="分支名称。")
    description: str = Field(default="", description="分支描述。")
    platform: dict[str, object] = Field(default_factory=dict, description="上游平台给出的分支信息。")
    meta: dict[str, Any] = Field(default_factory=dict, description="分支元信息，预留字段。")


class TaskPlanSpec(BaseModel):
    """任务方案，来源于其他系统或本地资源快照。

    TaskPlan 只描述业务侧任务意图、分支、目标和约束，不包含可执行 tick-agent 参数。
    """

    plan_id: str = Field(description="任务方案唯一标识。")
    name: str = Field(description="任务方案名称。")
    scenario_name: str = Field(description="想定名称或场景标识。")
    side: str = Field(description="执行规划的一方，例如 blue。")
    opponent_side: str = Field(default="", description="对抗方，例如 red。")
    objective: str = Field(default="", description="任务目标。")
    constraints: list[str] = Field(default_factory=list, description="任务约束。")
    branches: list[TaskBranchSpec] = Field(default_factory=list, description="任务方案分支。")
    meta: dict[str, Any] = Field(default_factory=dict, description="任务方案元信息，预留字段。")
