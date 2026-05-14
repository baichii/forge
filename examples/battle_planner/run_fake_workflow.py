"""Run the fake battle-planner parameter optimization workflow."""

from pathlib import Path
import sys


EXAMPLES_ROOT = Path(__file__).resolve().parents[1]
if str(EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_ROOT))

from battle_planner.orchestration.state.state import StrategyOptimizationState
from battle_planner.orchestration.workflow import BattlePlannerWorkflow
from battle_planner.utils.fake import (
    build_existing_strategy,
    build_fake_scenario,
    build_fake_tick_agent_definition,
)


def build_initial_state(max_iterations: int = 3) -> StrategyOptimizationState:
    return StrategyOptimizationState(
        strategy=build_existing_strategy(),
        tick_agent=build_fake_tick_agent_definition(),
        env_instance=build_fake_scenario(),
        max_iterations=max_iterations,
    )


def main() -> None:
    workflow = BattlePlannerWorkflow(max_iterations=3)
    final_state = workflow.run(build_initial_state(max_iterations=3))

    print("Fake battle planner workflow finished")
    print(f"iterations: {final_state.iteration}")
    print(f"stage: {final_state.cur_stage}")
    print("")

    for item in final_state.history:
        result = item["result"]
        params = item["params"]
        recommendation = item["recommendation"]
        print(f"iteration {item['iteration']}")
        print(f"  params: {params['params']}")
        print(f"  score: {result['score']}")
        print(f"  stats: {result['statistics']}")
        print(f"  key_events: {result['key_events'][:2]}")
        print(f"  advice: {recommendation['advice']}")
        print("")

    if final_state.best_result and final_state.best_params:
        print("best result")
        print(f"  iteration: {final_state.best_result.iteration}")
        print(f"  score: {final_state.best_result.score}")
        print(f"  params: {final_state.best_params.params}")


if __name__ == "__main__":
    main()
