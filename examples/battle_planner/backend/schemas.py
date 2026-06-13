"""Backend 接口视图模型。"""

from __future__ import annotations

from battle_planner.model import RunOutputStatus
from pydantic import BaseModel, Field


class TaskContextListItemView(BaseModel):
    """任务上下文列表项，用于前端选择已保存配置。"""

    context_id: str = Field(description="任务上下文唯一 ID。")
    name: str = Field(default="", description="任务上下文名称。")
    plan_id: str = Field(description="来源任务方案 ID。")
    plan_name: str = Field(description="任务方案名称。")
    scenario_name: str = Field(default="", description="想定名称或场景标识。")
    branch_count: int = Field(default=0, description="任务分支数量。")
    created_at: str = Field(default="", description="创建时间。")


class TaskRunListItemView(BaseModel):
    """任务运行列表项，用于前端选择历史任务。"""

    run_id: str = Field(description="任务运行唯一 ID。")
    run_name: str = Field(default="", description="任务运行名称。")
    context_id: str = Field(description="任务上下文 ID。")
    context_name: str = Field(default="", description="任务上下文名称。")
    plan_id: str = Field(description="来源任务方案 ID。")
    plan_name: str = Field(default="", description="任务方案名称。")
    status: RunOutputStatus = Field(default="created", description="运行状态。")
    iteration_count: int = Field(default=0, description="已完成迭代数量。")
    created_at: str = Field(default="", description="创建时间。")
