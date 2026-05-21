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
