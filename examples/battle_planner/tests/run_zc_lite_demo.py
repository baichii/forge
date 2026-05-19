"""Run the zc_lite battle-planner end-to-end demo."""

import sys
from pathlib import Path
from time import perf_counter

EXAMPLES_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]
for path in (REPO_ROOT, EXAMPLES_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from battle_planner.orchestration.workflow import BattlePlannerDemoWorkflow  # noqa: E402


def main() -> None:
    started_at = perf_counter()
    final_state = BattlePlannerDemoWorkflow().run()
    workflow_elapsed = perf_counter() - started_at

    print("Battle planner zc_lite demo finished")
    print(f"stage: {final_state.cur_stage}")
    print(f"scenario: {final_state.scenario_name}")
    print(f"workflow_elapsed_seconds: {workflow_elapsed:.4f}")
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
        elapsed_seconds = final_state.simulation_result.raw_summary.get("elapsed_seconds")
        if elapsed_seconds is not None:
            print(f"- elapsed_seconds: {float(elapsed_seconds):.4f}")
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
