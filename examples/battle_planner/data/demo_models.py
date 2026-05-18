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


class AgentParamSpec(BaseModel):
    name: str
    description: str
    type: str
    default: Any
    required: bool = True
    examples: list[Any] = Field(default_factory=list)


class FakeTickAgentSpec(BaseModel):
    name: str
    description: str
    applicable_scenarios: list[str] = Field(default_factory=list)
    params: list[AgentParamSpec] = Field(default_factory=list)


class PlannedAgentParams(BaseModel):
    agent_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


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
