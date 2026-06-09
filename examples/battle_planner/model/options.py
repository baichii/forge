from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskRunOptions(BaseModel):
    """一次完整策略迭代运行的配置。"""

    workflow_name: str = Field(default="", description="可选 workflow 名称；为空时使用部署配置。")
    max_iterations: int = Field(default=5, description="最大迭代轮数。")
    sim_runs_per_scheme: int = Field(default=1, description="每版方案的仿真次数。")
    max_retry: int = Field(default=1, description="最大重试次数。")
    timeout_seconds: int | None = Field(default=None, description="运行超时时间，单位秒。")
    extra: dict[str, Any] = Field(default_factory=dict, description="workflow 对外暴露的其他约束配置。")
