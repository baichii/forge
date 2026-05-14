"""strategy_plan_agent 的 LangGraph node 包装。"""

from battle_planner.ai.custom_agents.strategy_plan_agent import (
    StrategyPlanAgent,
    StrategyPlanAgentConfig,
)
from battle_planner.orchestration.state.state import (
    StrategyOptimizationState,
    WorkflowState,
)


def strategy_plan_node(state: StrategyOptimizationState) -> StrategyOptimizationState:
    agent = StrategyPlanAgent(StrategyPlanAgentConfig())
    next_iteration = state.iteration + 1
    params = agent.invoke(
        strategy=state.strategy,
        tick_agent=state.tick_agent,
        iteration=next_iteration,
        previous_params=state.current_params,
        recommendation=state.latest_recommendation,
    )

    state.iteration = next_iteration
    state.current_params = params
    state.update_stage(WorkflowState.STRATEGY_PLANNED)
    return state
