from langgraph.graph import END, StateGraph

from battle_planner.orchestration.nodes import (
    simulation_node,
    strategy_plan_node,
    summary_plan_node,
)
from battle_planner.orchestration.state.state import StrategyOptimizationState


class BattlePlannerWorkflow:
    """
    测试工作流

    Notes:
        1. 大幅简化场景, plan-> plan branch -> strategy 的流程直接优化为对策略进行优化
        2. langgraph-node部分节点先硬编码跑通流程

    """

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations

    def build_graph(self):
        builder = StateGraph(StrategyOptimizationState)

        builder.add_node("strategy_plan", strategy_plan_node)
        builder.add_node("simulation", simulation_node)
        builder.add_node("summary_plan", summary_plan_node)

        builder.set_entry_point("strategy_plan")
        builder.add_edge("strategy_plan", "simulation")
        builder.add_edge("simulation", "summary_plan")
        builder.add_conditional_edges(
            "summary_plan",
            route_after_summary,
            {
                "continue": "strategy_plan",
                "end": END,
            },
        )

        return builder.compile()

    def run(self, initial_state: StrategyOptimizationState) -> StrategyOptimizationState:
        graph = self.build_graph()
        result = graph.invoke(initial_state)
        return StrategyOptimizationState.model_validate(result)


def route_after_summary(state: StrategyOptimizationState) -> str:
    if state.error:
        return "end"
    if state.iteration >= state.max_iterations:
        return "end"
    if state.latest_recommendation is None:
        return "end"
    if not state.latest_recommendation.should_continue:
        return "end"
    return "continue"


def build_fake_optimization_graph():
    return BattlePlannerWorkflow().build_graph()
