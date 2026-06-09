from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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


class PlannerKnowledgePack(BaseModel):
    scenario_summary: dict[str, Any] = Field(default_factory=dict)
    planning_goal: PlanningGoal
    force_summary: dict[str, Any] = Field(default_factory=dict)
    asset_catalog: list[AssetSummary] = Field(default_factory=list)
    weapon_catalog: list[dict[str, Any]] = Field(default_factory=list)
    agent_capability_notes: list[str] = Field(default_factory=list)
    mission_schema_notes: list[str] = Field(default_factory=list)
    planning_constraints: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    evidence_refs: dict[str, str] = Field(default_factory=dict)
