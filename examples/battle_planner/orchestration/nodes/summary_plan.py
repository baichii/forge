"""summary_plan_agent 的 LangGraph node 包装。"""

from battle_planner.ai.custom_agents.summary_plan_agent import (
    SummaryPlanAgent,
    SummaryPlanAgentConfig,
)
from battle_planner.orchestration.state.state import (
    StrategyOptimizationState,
    WorkflowState,
)


def summary_plan_node(state: StrategyOptimizationState) -> StrategyOptimizationState:
    if state.current_params is None or state.latest_result is None:
        state.mark_error("summary_plan_node requires current_params and latest_result")
        return state

    agent = SummaryPlanAgent(SummaryPlanAgentConfig())
    recommendation = agent.invoke(
        result=state.latest_result,
        best_result=state.best_result,
        max_iterations=state.max_iterations,
    )

    state.latest_recommendation = recommendation
    state.record_iteration(
        params=state.current_params,
        result=state.latest_result,
        recommendation=recommendation,
    )
    if recommendation.should_continue and state.iteration < state.max_iterations:
        state.update_stage(WorkflowState.SUMMARY_FINISHED)
    else:
        state.update_stage(WorkflowState.COMPLETE)
    return state
