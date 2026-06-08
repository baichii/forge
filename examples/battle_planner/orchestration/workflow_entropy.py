from typing import ClassVar

from battle_planner.config import config
from battle_planner.orchestration.workflow.zc_lite_baseline import ZcLiteBaselineWorkflow


class WorkflowEntropy:
    """Manual workflow builder for explicitly imported workflow implementations."""

    workflow_types: ClassVar[dict[str, type[ZcLiteBaselineWorkflow]]] = {
        ZcLiteBaselineWorkflow.name: ZcLiteBaselineWorkflow,
    }

    @classmethod
    def build_workflow(cls, name: str | None = None) -> ZcLiteBaselineWorkflow:
        workflow_name = name or config.runtime.workflow_name
        try:
            workflow_type = cls.workflow_types[workflow_name]
        except KeyError as exc:
            available = ", ".join(sorted(cls.workflow_types))
            raise ValueError(
                f"Unknown battle planner workflow: {workflow_name}. Available: {available}"
            ) from exc
        return workflow_type()

    @classmethod
    def build_graph(cls, name: str | None = None):
        return cls.build_workflow(name).build_graph()


def build_workflow(name: str | None = None) -> ZcLiteBaselineWorkflow:
    return WorkflowEntropy.build_workflow(name)


def build_graph(name: str | None = None):
    return WorkflowEntropy.build_graph(name)
