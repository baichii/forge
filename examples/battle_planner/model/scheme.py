"""可执行方案模型预留。

这里的 Scheme 与外部 scheme 平台语义保持一致：它是可执行方案，包含完整运行参数。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from forge.core.specs import CallbackParams, TickAgentParams


class SchemeBranchExecutionSpec(BaseModel):
    """某个方案分支绑定的 tick-agent 运行参数。"""

    branch_id: int = Field(description="来源任务分支 ID。")
    planned_agent_params: list[TickAgentParams] = Field(
        default_factory=list, description="该分支绑定的 tick-agent 参数。"
    )
    meta: dict[str, Any] = Field(default_factory=dict, description="预留字段。")


class SchemeSpec(BaseModel):
    """LLM 迭代生成的一版可执行方案。

    Notes:
        为matrix预留

    """

    scheme_id: int = Field(description="可执行方案 ID，在所属任务运行内从 1 开始自增。")
    run_id: str = Field(description="来源任务运行 ID。")
    branch_executions: list[SchemeBranchExecutionSpec] = Field(
        default_factory=list, description="分支到 tick-agent 参数的绑定关系。"
    )
    callback_params: list[CallbackParams] = Field(default_factory=list, description="callback 参数。")
    meta: dict[str, Any] = Field(default_factory=dict, description="方案元信息，预留字段。")
