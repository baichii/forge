"""外部或本地入口请求模型。"""

from __future__ import annotations

from typing import Any

from battle_planner.model.human import BranchHumanInputSpec, PlanHumanInputSpec
from pydantic import BaseModel, Field


class TaskBranchHumanInputRequest(BaseModel):
    """任务分支的人工输入。"""

    branch_id: int = Field(description="来源任务分支 ID，在所属任务方案内从 1 开始自增。")
    human: BranchHumanInputSpec = Field(default_factory=BranchHumanInputSpec, description="分支人工输入。")


class TaskContextCreateRequest(BaseModel):
    """创建任务上下文的请求。

    TaskContext = TaskPlan + human input，是后续 LLM 迭代的上下文输入。
    """

    plan_id: str = Field(description="来源任务方案 ID。")
    name: str = Field(default="", description="任务上下文名称。")
    plan_human: PlanHumanInputSpec = Field(
        default_factory=PlanHumanInputSpec, description="任务方案层人工输入。"
    )
    branch_humans: list[TaskBranchHumanInputRequest] = Field(
        default_factory=list, description="任务分支人工输入。"
    )


class TaskRunCreateRequest(BaseModel):
    """创建一次任务运行的请求。"""

    context_id: str = Field(description="任务上下文 ID。")
    run_name: str = Field(default="", description="任务运行名称，用于内部日志生成。")
    options: dict[str, Any] = Field(default_factory=dict, description="运行参数原始输入。")
