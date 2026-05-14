"""fake 仿真运行 LangGraph node。"""

from battle_planner.data.models import SimulationResult
from battle_planner.orchestration.state.state import (
    StrategyOptimizationState,
    WorkflowState,
)
from battle_planner.utils.fake import FakeEnv, FakeSimulationRunner, build_fake_tick_agent


def simulation_node(state: StrategyOptimizationState) -> StrategyOptimizationState:
    if state.current_params is None:
        state.mark_error("simulation_node requires current_params")
        return state

    env = FakeEnv(
        env_instance=state.env_instance,
    )
    agent = build_fake_tick_agent(state.current_params.params)
    runner = FakeSimulationRunner(env=env, agent=agent)
    raw_result = runner.run()
    result = SimulationResult(
        iteration=state.iteration,
        params=state.current_params.params,
        logs=raw_result["logs"],
        key_events=raw_result["key_events"],
        statistics=raw_result["statistics"],
        score=raw_result["score"],
    )

    state.latest_result = result
    state.update_stage(WorkflowState.SIM_FINISHED)
    return state
