from __future__ import annotations

from typing import Any

from battle_planner.model.simulation import EvaluationReport, SimulationRunResult
from pydantic import BaseModel, Field


class LLMTrace(BaseModel):
    node_name: str
    input_messages: list[dict[str, Any]] = Field(default_factory=list)
    raw_output: str = ""
    parsed_output: Any | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None


class EvaluationAggregateSpec(BaseModel):
    """多次仿真评估后的聚合结果。"""

    case_count: int = 0
    metric_summary: dict[str, Any] = Field(default_factory=dict)


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
