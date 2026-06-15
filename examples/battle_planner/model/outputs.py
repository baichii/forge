from __future__ import annotations

from typing import Any, Literal

from battle_planner.model.scheme import SchemeSpec
from battle_planner.model.simulation import SimulationRunResult
from pydantic import BaseModel, Field

from forge.core.specs import CallbackParams, TickAgentParams

RunOutputStatus = Literal["created", "running", "completed", "failed", "cancelled"]
RunIterationStatus = Literal["pending", "running", "completed", "failed", "skipped"]
RunArtifactContentType = Literal["markdown", "json", "text"]
RunArtifactType = Literal[
    "scenario_understanding",
    "battle_plan",
    "agent_params",
    "scheme",
    "deduction",
    "simulation_result",
    "evaluation_report",
    "evaluation_summary",
    "summary",
    "harness_trace",
]


class RunTextSummarySpec(BaseModel):
    """LLM 或规则生成的短文本摘要。"""

    label: str = Field(default="", description="短标签。")
    title: str = Field(default="", description="标题。")
    summary: str = Field(default="", description="摘要文本。")


class RunIterationTagSpec(BaseModel):
    """用于辅助选择轮次的业务标签。"""

    key: str = Field(description="标签键，例如 exploration、best_so_far、stable。")
    label: str = Field(description="展示标签，例如探索、当前最佳、稳定。")
    reason: str = Field(default="", description="标签判定原因。")


class RunArtifactSpec(BaseModel):
    """一次运行或某轮迭代产生的可追溯产物。"""

    artifact_id: str = Field(description="产物 ID。")
    artifact_type: RunArtifactType = Field(description="产物类型。")
    title: str = Field(default="", description="产物标题。")
    content_type: RunArtifactContentType = Field(default="json", description="产物内容类型。")
    payload: dict[str, Any] | str = Field(default_factory=dict, description="产物内容。")
    text_summary: RunTextSummarySpec | None = Field(default=None, description="产物短文本摘要。")
    run_id: str | None = Field(default=None, description="任务运行 ID。")
    iteration_index: int | None = Field(default=None, description="所属迭代序号。")
    meta: dict[str, Any] = Field(default_factory=dict, description="预留扩展字段。")


class RunSimulationRecordSpec(BaseModel):
    """同一轮迭代内的一次仿真验证记录。"""

    simulation_index: int = Field(default=0, description="同一轮迭代内的仿真序号。")
    seed: int | None = Field(default=None, description="随机种子。")
    simulation_result: SimulationRunResult | None = Field(default=None, description="仿真结果。")
    summary: RunTextSummarySpec | None = Field(default=None, description="本次仿真事实摘要。")
    meta: dict[str, Any] = Field(default_factory=dict, description="预留扩展字段。")


class RunIterationOutputSpec(BaseModel):
    """某轮策略迭代的展示摘要。"""

    # 基础信息
    iteration_index: int = Field(description="迭代序号。")
    status: RunIterationStatus = Field(default="pending", description="轮次状态。")
    iteration_tags: list[RunIterationTagSpec] = Field(default_factory=list, description="轮次业务标签。")

    # 总结信息
    overall_summary: RunTextSummarySpec | None = Field(
        default=None,
        description="截至本轮的总体摘要，可包含 session 现状分析。",
    )
    effect_summary: RunTextSummarySpec | None = Field(default=None, description="本轮效果摘要。")
    report_summary: RunTextSummarySpec | None = Field(default=None, description="本轮仿真报告摘要。")
    decision_summary: RunTextSummarySpec | None = Field(default=None, description="本轮决策建议摘要。")

    # 方案与运行参数
    scheme: SchemeSpec | None = Field(default=None, description="本轮执行方案。")

    # 仿真验证结果
    simulation_runs: list[RunSimulationRecordSpec] = Field(
        default_factory=list,
        description="本轮仿真验证记录。",
    )

    meta: dict[str, Any] = Field(default_factory=dict, description="预留扩展字段。")


class RunOutputSpec(BaseModel):
    """一次任务运行的完整输出快照。"""

    # 基础字段， 来自plan 和plan human input
    run_id: str = Field(description="任务运行 ID。")
    run_name: str = Field(description="任务运行名称。")
    context_id: str = Field(description="任务上下文 ID。")
    context_name: str = Field(description="任务上下文名称")
    plan_id: str = Field(description="任务方案 ID。")
    plan_name: str = Field(description="任务方案名称。")
    scenario_name: str = Field(default="", description="想定或场景名称。")
    objective: str = Field(default="", description="本次运行的业务目标。")
    max_iterations: int | None = Field(default=None, description="最大迭代轮数。")

    # session 级信息
    status: RunOutputStatus = Field(default="created", description="运行状态。")
    started_at: str = Field(default="", description="任务开始时间。")
    ended_at: str | None = Field(default=None, description="任务结束时间。")

    # iteration级信息
    iterations: list[RunIterationOutputSpec] = Field(default_factory=list, description="迭代输出摘要列表。")

    meta: dict[str, Any] = Field(default_factory=dict, description="预留扩展字段。")
