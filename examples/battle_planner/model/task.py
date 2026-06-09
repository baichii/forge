"""TaskPlan -> TaskContext -> TaskRun 的核心实体和转换函数。"""

from __future__ import annotations

from typing import Any

from battle_planner.model.human import BranchHumanInputSpec, PlanHumanInputSpec
from battle_planner.model.options import TaskRunOptions
from pydantic import BaseModel, Field


class TaskBranchContextSpec(BaseModel):
    """任务分支上下文，包含分支身份和最终人工配置。"""

    branch_id: int = Field(description="来源任务分支 ID。")
    name: str = Field(description="分支名称。")
    description: str = Field(default="", description="分支描述。")
    human: BranchHumanInputSpec = Field(default_factory=BranchHumanInputSpec, description="分支人工输入。")
    meta: dict[str, Any] = Field(default_factory=dict, description="分支元信息，预留字段。")


class TaskContextSpec(BaseModel):
    """任务上下文，作为 LLM 策略迭代的输入上下文。"""

    context_id: str = Field(description="任务上下文唯一 ID。")
    plan_id: str = Field(description="来源任务方案 ID。")
    name: str = Field(default="", description="任务上下文名称。")
    plan_name: str = Field(description="任务方案名称。")
    scenario_name: str = Field(description="想定名称或场景标识。")
    side: str = Field(description="执行规划的一方，例如 blue。")
    opponent_side: str = Field(default="", description="对抗方，例如 red。")
    human: PlanHumanInputSpec = Field(
        default_factory=PlanHumanInputSpec, description="任务方案层人工输入。"
    )
    branches: list[TaskBranchContextSpec] = Field(default_factory=list, description="任务分支上下文。")
    meta: dict[str, Any] = Field(default_factory=dict, description="任务上下文元信息，预留字段。")


class TaskRunSpec(BaseModel):
    """一次完整策略迭代运行。"""

    run_id: str = Field(description="任务运行唯一 ID。")
    context_id: str = Field(description="任务上下文 ID。")
    plan_id: str = Field(description="来源任务方案 ID。")
    run_name: str = Field(default="", description="任务运行名称，用于内部日志生成。")
    task_context: TaskContextSpec = Field(description="任务运行上下文。")
    options: TaskRunOptions = Field(description="运行配置。")
    meta: dict[str, Any] = Field(default_factory=dict, description="任务运行元信息，预留字段。")
