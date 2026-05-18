"""Run the zc_lite battle-planner end-to-end demo."""

from pathlib import Path
import sys


EXAMPLES_ROOT = Path(__file__).resolve().parents[1]
if str(EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_ROOT))

from battle_planner.orchestration.workflow import BattlePlannerDemoWorkflow


def main() -> None:
    final_state = BattlePlannerDemoWorkflow().run()

    print("Battle planner zc_lite demo finished")
    print(f"stage: {final_state.cur_stage}")
    print(f"scenario: {final_state.scenario_name}")
    if final_state.error:
        print(f"error: {final_state.error}")
        return

    print("")
    print("planned agent params")
    for item in final_state.planned_agent_params:
        print(f"- {item.agent_name}: {item.params}")

    if final_state.simulation_result:
        print("")
        print("simulation")
        print(f"- steps: {final_state.simulation_result.steps}")
        print(f"- done: {final_state.simulation_result.done}")
        for log in final_state.simulation_result.logs:
            print(f"  {log}")

    if final_state.evaluation_report:
        print("")
        print("evaluation")
        print(f"- score: {final_state.evaluation_report.score}")
        print(f"- advice: {final_state.evaluation_report.advice}")

    print("")
    print("llm traces")
    for trace in final_state.llm_traces:
        print(
            f"- {trace.node_name}: fallback={trace.fallback_used} "
            f"raw_len={len(trace.raw_output)} error={trace.error}"
        )

    print("")
    print("summary")
    print(final_state.summary_md)


if __name__ == "__main__":
    main()
