"""Compatibility exports for battle planner model classes.

New code should import from the semantic modules in this package.
"""

from battle_planner.model.deduction import DeductionSpec
from battle_planner.model.evaluation import (
    AgentExecutionSummary,
    EvaluationAggregateSpec,
    EvaluationFailureReason,
    LLMTrace,
    SummaryEvaluation,
    TargetObjectiveSummary,
)
from battle_planner.model.human import (
    BranchHumanInputSpec,
    PlanHumanInputSpec,
    RiskStyle,
)
from battle_planner.model.knowledge import (
    AssetSummary,
    PlannerKnowledgePack,
    PlanningGoal,
)
from battle_planner.model.options import TaskRunOptions
from battle_planner.model.outputs import (
    RunArtifactSpec,
    RunIterationOutputSpec,
    RunIterationTagSpec,
    RunOutputSpec,
    RunOutputStatus,
    RunSimulationRecordSpec,
    RunTextSummarySpec,
)
from battle_planner.model.requests import (
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
)
from battle_planner.model.scheme import SchemeBranchExecutionSpec, SchemeSpec
from battle_planner.model.simulation import EvaluationFindingSpec, EvaluationReport, SimulationRunResult
from battle_planner.model.source import TaskBranchSpec, TaskPlanSpec, TickAgentSourceSpec
from battle_planner.model.task import (
    TaskBranchContextSpec,
    TaskContextSpec,
    TaskRunSpec,
)

__all__ = [
    "AgentExecutionSummary",
    "AssetSummary",
    "BranchHumanInputSpec",
    "DeductionSpec",
    "EvaluationAggregateSpec",
    "EvaluationFailureReason",
    "EvaluationFindingSpec",
    "EvaluationReport",
    "LLMTrace",
    "PlanHumanInputSpec",
    "PlannerKnowledgePack",
    "PlanningGoal",
    "RiskStyle",
    "RunArtifactSpec",
    "RunIterationOutputSpec",
    "RunIterationTagSpec",
    "RunOutputSpec",
    "RunOutputStatus",
    "RunSimulationRecordSpec",
    "RunTextSummarySpec",
    "SchemeSpec",
    "SchemeBranchExecutionSpec",
    "SimulationRunResult",
    "SummaryEvaluation",
    "TaskBranchContextSpec",
    "TaskBranchHumanInputRequest",
    "TaskBranchSpec",
    "TaskContextCreateRequest",
    "TaskContextSpec",
    "TaskPlanSpec",
    "TaskRunCreateRequest",
    "TaskRunOptions",
    "TaskRunSpec",
    "TargetObjectiveSummary",
    "TickAgentSourceSpec",
]
