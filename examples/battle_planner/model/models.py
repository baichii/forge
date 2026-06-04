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


class TargetObjectiveSummary(BaseModel):
    """Summary evaluator 生成的目标状态摘要。"""

    target_id: str
    alive: bool = True
    initial_health: int | float | None = None
    current_health: int | float | None = None
    health_delta: int | float | None = None
    health_percent_delta: int | float | None = None
    achieved: bool = False


class AgentExecutionSummary(BaseModel):
    """Summary evaluator 生成的 agent 执行摘要。"""

    agent_instance_id: str
    agent_name: str
    side: str
    action_count: int = 0
    executed: bool = False
    first_active_step: int | None = None
    finished_step: int | None = None
    issue: str = ""


class SummaryEvaluation(BaseModel):
    """Summary node 对单轮 runtime report 的结构化理解结果。"""

    iteration_index: int = 0
    objective: str = ""
    objective_achieved: bool = False
    target_status: list[TargetObjectiveSummary] = Field(default_factory=list)
    agent_execution: list[AgentExecutionSummary] = Field(default_factory=list)
    inactive_agents: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    advice: str = ""


class HumanInputSpec(BaseModel):
    """人工输入的约束、偏好或补充说明。"""

    summary: str = Field(default="", description="人工输入摘要。")
    items: list[str] = Field(default_factory=list, description="人工输入条目。")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="人工输入原始内容。")


class PlatformTacticSpec(BaseModel):
    """上游平台生成的打法信息。"""

    summary: str = Field(default="", description="上游平台生成的打法摘要。")
    items: list[str] = Field(default_factory=list, description="打法、阶段、目标或约束条目。")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="上游平台原始内容。")


class StrategySpec(BaseModel):
    """策略分支：描述一个可审阅的打法方案。

    Strategy 只承载分支语义，不直接承载 runner 执行参数。
    """

    strategy_id: str = Field(description="策略唯一标识。")
    name: str = Field(description="策略名称，用于平台卡片展示和人工审阅。")
    description: str = Field(default="", description="策略描述，用自然语言说明该策略如何完成方案目标。")
    platform: PlatformTacticSpec = Field(
        default_factory=PlatformTacticSpec, description="上游平台打法信息。"
    )
    human: HumanInputSpec = Field(default_factory=HumanInputSpec, description="人工输入的策略补充。")
    meta: dict[str, Any] = Field(default_factory=dict, description="策略元信息，预留字段。")


class SchemeSpec(BaseModel):
    """方案：描述一次方案规划任务及其多个策略分支。

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
    human: HumanInputSpec = Field(default_factory=HumanInputSpec, description="人工输入的全局补充。")
    meta: dict[str, Any] = Field(default_factory=dict, description="方案元信息，预留字段。")


class StrategyParam(BaseModel):
    """单个策略分支生成后的运行时参数。

    默认应用场景是单 focal strategy 优化；本层 callback 用于评价该策略自身的目标达成情况。
    """

    strategy_id: str = Field(description="来源策略 id。")
    status: str = Field(default="draft", description="生成状态。")
    summary: str = Field(default="", description="策略运行参数摘要。")
    agent_configs: list[dict[str, Any]] = Field(default_factory=list, description="生成后的 agent 配置。")
    callback_configs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="策略评价 callback 配置；只评价该 strategy 的目标达成情况，不评价其他环境策略。",
    )
    warnings: list[str] = Field(default_factory=list, description="策略参数生成过程中的警告。")
    artifacts: list[dict[str, Any]] = Field(default_factory=list, description="策略参数生成过程产物。")
    meta: dict[str, Any] = Field(default_factory=dict, description="策略参数元信息，预留字段。")


class DeductionSpec(BaseModel):
    """一个方案下所有策略分支生成后的推演/执行信息。

    Deduction 层描述整次运行的共享环境和全局观测；策略优化指标归入对应 StrategyParam。
    """

    deduction_id: str = Field(description="推演唯一标识。")
    scheme_id: str = Field(description="所属方案 id。")
    status: str = Field(default="draft", description="整体生成状态。")
    summary: str = Field(default="", description="整体生成结果摘要。")
    env_config: dict[str, Any] = Field(default_factory=dict, description="生成后的环境配置。")
    runtime_hooks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="整次 deduction 的全局运行观测配置，例如日志、trace 或 step metric，不用于单策略评价。",
    )
    strategy_params: list[StrategyParam] = Field(
        default_factory=list, description="各策略分支对应的运行时参数。"
    )
    warnings: list[str] = Field(default_factory=list, description="生成过程中的警告。")
    artifacts: list[dict[str, Any]] = Field(default_factory=list, description="生成过程产物。")
    meta: dict[str, Any] = Field(default_factory=dict, description="推演元信息，预留字段。")


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
