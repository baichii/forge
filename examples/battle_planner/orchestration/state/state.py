import uuid
from typing import Any
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field

from battle_planner.data.models import (
    EnvInstance,
    SimulationResult,
    Strategy,
    StrategyParameterSet,
    StrategyRecommendation,
    TickAgent,
)


class WorkflowState(StrEnum):
    """定义业务状态推进情况状态"""
    START = "start"
    COMPLETE = "complete"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    STRATEGY_PLANNED = "strategy_planned"
    SIM_FINISHED = "sim_finished"
    SUMMARY_FINISHED = "summary_finished"


class StrategyPlanningState(BaseModel):
    """
    策略迭代状态记录

    """

    # Workflow state management
    cur_stage: WorkflowState = WorkflowState.START
    previous_state: WorkflowState | None = None
    start_time: datetime | None = None
    last_update_time: datetime | None = None
    stage_times: dict[str, datetime] = Field(default_factory=dict)

    # Error handling and recovery
    error: str | None = None
    error_count: int = 0
    retry_count: dict[str, int] = Field(default_factory=dict)

    # Interruption handling
    interrupted: bool = False
    interruption_reason: str | None = None
    checkpoint_id: str | None = None

    # Progress tracking
    progress: float = 0.0  # 0.0 to 1.0
    stage_progress: dict[str, float] = Field(default_factory=dict)

    # Parallel execution tracking
    parallel_tasks: list[str] = Field(default_factory=list)
    completed_tasks: list[str] = Field(default_factory=list)
    task_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class StrategyOptimizationState(BaseModel):
    """LangGraph 中流转的 fake 策略参数迭代状态。"""

    strategy: Strategy
    tick_agent: TickAgent
    env_instance: EnvInstance
    max_iterations: int = 3

    iteration: int = 0
    cur_stage: WorkflowState = WorkflowState.START
    current_params: StrategyParameterSet | None = None
    latest_result: SimulationResult | None = None
    latest_recommendation: StrategyRecommendation | None = None
    best_result: SimulationResult | None = None
    best_params: StrategyParameterSet | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)

    start_time: datetime | None = None
    last_update_time: datetime | None = None
    stage_times: dict[str, datetime] = Field(default_factory=dict)
    error: str | None = None
    error_count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        now = datetime.now()
        if self.start_time is None:
            self.start_time = now
        self.last_update_time = now
        self.stage_times.setdefault(str(self.cur_stage), now)

    def update_stage(self, new_stage: WorkflowState) -> None:
        self.cur_stage = new_stage
        now = datetime.now()
        self.last_update_time = now
        self.stage_times[str(new_stage)] = now

    def record_iteration(
        self,
        params: StrategyParameterSet,
        result: SimulationResult,
        recommendation: StrategyRecommendation,
    ) -> None:
        self.history.append(
            {
                "iteration": result.iteration,
                "params": params.model_dump(),
                "result": result.model_dump(),
                "recommendation": recommendation.model_dump(),
            }
        )
        if self.best_result is None or result.score > self.best_result.score:
            self.best_result = result
            self.best_params = params

    def mark_error(self, error_message: str) -> None:
        self.error = error_message
        self.error_count += 1
        self.update_stage(WorkflowState.ERROR)
