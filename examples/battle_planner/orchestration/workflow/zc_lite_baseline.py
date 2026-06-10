from typing import ClassVar

from battle_planner.orchestration.nodes import (
    agent_parameter_planning_node,
    agent_schema_loading_node,
    battle_plan_generation_node,
    evaluation_node,
    prepare_scenario_node,
    scenario_understanding_node,
    simulation_node,
    summary_node,
)
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from langgraph.graph import END, StateGraph


class ZcLiteBaselineWorkflow:
    """End-to-end zc_lite demo workflow with LLM-visible stages."""

    name: ClassVar[str] = "zc_lite_baseline"

    def build_graph(self):
        builder = StateGraph(BattlePlannerState)

        builder.add_node(WorkflowStages.SCENARIO_PREPARATION, prepare_scenario_node)
        builder.add_node(WorkflowStages.SCENARIO_UNDERSTANDING, scenario_understanding_node)
        builder.add_node(WorkflowStages.BATTLE_PLAN_GENERATION, battle_plan_generation_node)
        builder.add_node(WorkflowStages.AGENT_SCHEMA_LOADING, agent_schema_loading_node)
        builder.add_node(WorkflowStages.AGENT_PARAMETER_PLANNING, agent_parameter_planning_node)
        builder.add_node(WorkflowStages.SIMULATION_EXECUTION, simulation_node)
        builder.add_node(WorkflowStages.RESULT_EVALUATION, evaluation_node)
        builder.add_node(WorkflowStages.SUMMARY_GENERATION, summary_node)

        builder.set_entry_point(WorkflowStages.SCENARIO_PREPARATION)
        builder.add_edge(WorkflowStages.SCENARIO_PREPARATION, WorkflowStages.SCENARIO_UNDERSTANDING)
        builder.add_edge(WorkflowStages.SCENARIO_UNDERSTANDING, WorkflowStages.BATTLE_PLAN_GENERATION)
        builder.add_edge(WorkflowStages.BATTLE_PLAN_GENERATION, WorkflowStages.AGENT_SCHEMA_LOADING)
        builder.add_edge(WorkflowStages.AGENT_SCHEMA_LOADING, WorkflowStages.AGENT_PARAMETER_PLANNING)
        builder.add_edge(WorkflowStages.AGENT_PARAMETER_PLANNING, WorkflowStages.SIMULATION_EXECUTION)
        builder.add_conditional_edges(
            WorkflowStages.SIMULATION_EXECUTION,
            route_after_demo_step,
            {
                "continue": WorkflowStages.RESULT_EVALUATION,
                "end": END,
            },
        )
        builder.add_conditional_edges(
            WorkflowStages.RESULT_EVALUATION,
            route_after_demo_step,
            {
                "continue": WorkflowStages.SUMMARY_GENERATION,
                "end": END,
            },
        )
        builder.add_edge(WorkflowStages.SUMMARY_GENERATION, END)

        return builder.compile()

    def run(self, initial_state: BattlePlannerState | None = None) -> BattlePlannerState:
        graph = self.build_graph()
        result = graph.invoke(initial_state or BattlePlannerState())
        return BattlePlannerState.model_validate(result)


def route_after_demo_step(state: BattlePlannerState) -> str:
    if state.error:
        return "end"
    return "continue"
