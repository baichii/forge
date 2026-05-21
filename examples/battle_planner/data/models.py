from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LLMTrace(BaseModel):
    node_name: str
    input_messages: list[dict[str, Any]] = Field(default_factory=list)
    raw_output: str = ""
    parsed_output: Any | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None


class SimulationRunResult(BaseModel):
    scenario_name: str
    steps: int
    done: bool
    logs: list[str] = Field(default_factory=list)
    raw_summary: dict[str, Any] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    score: float
    hard_violations: list[str] = Field(default_factory=list)
    mission_metrics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    diagnostic_events: list[dict[str, Any]] = Field(default_factory=list)
    advice: str = ""


class SchemeSpec(BaseModel):
    """上游业务输入：描述一次方案规划任务的目标、约束和优化方向。

    Scheme 面向平台、人工审阅和上游 LLM 生成，不直接承载 runner 执行参数。
    """

    scheme_id: str = Field(description="方案唯一标识，用于追踪本次规划任务。")
    name: str = Field(description="方案名称，便于平台展示和人工审阅。")
    scenario_name: str = Field(description="想定名称或场景标识。")
    side: str = Field(description="执行规划的一方，例如 blue。")
    opponent_side: str = Field(default="", description="对抗方，例如 red。")
    objective: str = Field(description="主要作战目标，例如摧毁红方航母。")
    constraints: list[str] = Field(default_factory=list, description="方案规划必须满足的业务约束。")
    strategies: list[StrategySpec] = Field(default_factory=list, description="这个方案配置的业务卡片")
    extra: str = Field(default_factory=str, description="额外信息")


class StrategySpec(BaseModel):
    """策略卡片：描述一个可审阅的策略方案。

    Strategy 先只承载方案语义，不直接承载 runner 执行参数。
    """

    strategy_id: str = Field(description="策略唯一标识。")
    name: str = Field(description="策略名称，用于平台卡片展示和人工审阅。")
    description: str = Field(default="", description="策略描述，用自然语言说明该策略如何完成方案目标。")
    target_ids: list[str] = Field(default_factory=list, description="该策略关注的目标 id。")


class PlanningGoal(BaseModel):
    assumptions: list[str] = Field(default_factory=list)
    scenario_assumptions: list[str] = Field(default_factory=list)
    objective: str
    constraints: list[str] = Field(default_factory=list)
    optimization_objective: str


class AssetSummary(BaseModel):
    side: str
    asset_id: str
    name: str
    prototype: str
    asset_type: str
    position: Any | None = None
    weapons: list[dict[str, Any]] = Field(default_factory=list)
    aircrafts: list[dict[str, Any]] = Field(default_factory=list)


class CapabilitySummary(BaseModel):
    capability: str
    agent_name: str
    subject: str
    target: str
    action_type: str
    required_fields: list[str] = Field(default_factory=list)
    rationale: str = ""
    confidence: float = 1.0


class MissionSchemaSummary(BaseModel):
    mission_type: str
    description: str
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    example: dict[str, Any] = Field(default_factory=dict)


class PlannerKnowledgePack(BaseModel):
    scenario_summary: dict[str, Any] = Field(default_factory=dict)
    planning_goal: PlanningGoal
    force_summary: dict[str, Any] = Field(default_factory=dict)
    asset_catalog: list[AssetSummary] = Field(default_factory=list)
    weapon_catalog: list[dict[str, Any]] = Field(default_factory=list)
    capability_catalog: list[CapabilitySummary] = Field(default_factory=list)
    mission_schema_catalog: list[MissionSchemaSummary] = Field(default_factory=list)
    planning_constraints: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    evidence_refs: dict[str, str] = Field(default_factory=dict)
