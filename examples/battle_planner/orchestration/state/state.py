from typing import Any

from battle_planner.model import (
    EvaluationReport,
    LLMTrace,
    PlannerKnowledgePack,
    SimulationRunResult,
    SummaryEvaluation,
    TaskContextSpec,
    TaskRunOptions,
    TaskRunSpec,
)
from pydantic import BaseModel, Field

from forge.core.specs import CallbackParams, TickAgentParams, TickAgentSpec


class BattlePlannerState(BaseModel):
    """Serializable state for the zc_lite end-to-end demo workflow."""

    plan_id: str | None = None
    context_id: str | None = None
    run_id: str | None = None
    task_context: TaskContextSpec | None = None
    task_run_options: TaskRunOptions | None = None
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


def build_initial_state(task_run: TaskRunSpec) -> BattlePlannerState:
    """从 TaskRun 构建 workflow 初始状态。

    Args:
        task_run: 本次策略迭代运行输入。

    Returns:
        workflow 可直接执行的初始状态。
    """

    task_context = task_run.task_context
    return BattlePlannerState(
        plan_id=task_run.plan_id,
        context_id=task_run.context_id,
        run_id=task_run.run_id,
        task_context=task_context,
        task_run_options=task_run.options,
        scenario_name=task_context.scenario_name,
    )
