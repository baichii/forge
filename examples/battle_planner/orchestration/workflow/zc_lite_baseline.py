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
from battle_planner.orchestration.state.state import BattlePlannerState
from langgraph.graph import END, StateGraph


class ZcLiteBaselineWorkflow:
    """End-to-end zc_lite demo workflow with LLM-visible stages."""

    name: ClassVar[str] = "zc_lite_baseline"

    def build_graph(self):
        builder = StateGraph(BattlePlannerState)

        builder.add_node("prepare_scenario", prepare_scenario_node)
        builder.add_node("scenario_understanding", scenario_understanding_node)
        builder.add_node("battle_plan_generation", battle_plan_generation_node)
        builder.add_node("agent_schema_loading", agent_schema_loading_node)
        builder.add_node("agent_parameter_planning", agent_parameter_planning_node)
        builder.add_node("simulation", simulation_node)
        builder.add_node("evaluation", evaluation_node)
        builder.add_node("summary", summary_node)

        builder.set_entry_point("prepare_scenario")
        builder.add_edge("prepare_scenario", "scenario_understanding")
        builder.add_edge("scenario_understanding", "battle_plan_generation")
        builder.add_edge("battle_plan_generation", "agent_schema_loading")
        builder.add_edge("agent_schema_loading", "agent_parameter_planning")
        builder.add_edge("agent_parameter_planning", "simulation")
        builder.add_conditional_edges(
            "simulation",
            route_after_demo_step,
            {
                "continue": "evaluation",
                "end": END,
            },
        )
        builder.add_conditional_edges(
            "evaluation",
            route_after_demo_step,
            {
                "continue": "summary",
                "end": END,
            },
        )
        builder.add_edge("summary", END)

        return builder.compile()

    def run(self, initial_state: BattlePlannerState | None = None) -> BattlePlannerState:
        graph = self.build_graph()
        result = graph.invoke(initial_state or BattlePlannerState())
        return BattlePlannerState.model_validate(result)


def route_after_demo_step(state: BattlePlannerState) -> str:
    if state.error:
        return "end"
    return "continue"
