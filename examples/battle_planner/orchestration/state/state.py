from typing import Any

from battle_planner.data.models import (
    EvaluationReport,
    LLMTrace,
    PlannerKnowledgePack,
    SimulationRunResult,
    SummaryEvaluation,
)
from pydantic import BaseModel, Field

from forge.core.specs import CallbackParams, TickAgentParams, TickAgentSpec


class BattlePlannerState(BaseModel):
    """Serializable state for the zc_lite end-to-end demo workflow."""

    scenario_name: str | None = None
    scenario_conf: dict[str, Any] = Field(default_factory=dict)
    scenario_conf_summary: dict[str, Any] = Field(default_factory=dict)
    planner_knowledge_pack: PlannerKnowledgePack | None = None
    scenario_understanding_md: str = ""
    battle_plan_md: str = ""
    tick_agent_specs: list[TickAgentSpec] = Field(default_factory=list)
    available_tools: list[dict[str, Any]] = Field(default_factory=list)
    planned_agent_params: list[TickAgentParams] = Field(default_factory=list)
    callback_params: list[CallbackParams] = Field(default_factory=list)
    iteration_index: int = 0
    history: list[dict[str, Any]] = Field(default_factory=list)
    agent_param_source: str = ""
    agent_param_preset_id: str | None = None
    simulation_result: SimulationRunResult | None = None
    evaluation_report: EvaluationReport | None = None
    summary_evaluation: SummaryEvaluation | None = None
    summary_md: str = ""
    llm_traces: list[LLMTrace] = Field(default_factory=list)
    error: str | None = None
    cur_stage: str = "start"

    def add_trace(self, trace: LLMTrace) -> None:
        self.llm_traces.append(trace)

    def mark_error(self, error_message: str) -> None:
        self.error = error_message
        self.cur_stage = "error"
