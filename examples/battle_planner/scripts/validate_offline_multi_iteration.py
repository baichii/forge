"""离线多轮 workflow 验证.

Notes:
    用于快速查看 offline seed 与真实仿真链路是否能连续运行。
"""

from __future__ import annotations

import json
from typing import Any

from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.scripts.run_offline import run_offline_iterations

MAX_ITERATIONS = 5
SIM_MAX_DECISION_STEPS: int | None = 70
OUTPUT_SEED = "debug"
VERBOSE = 1
PRINT_EVENTS = False
PRINT_JSON = False


def main() -> None:
    result = run_offline_iterations(
        max_iterations=MAX_ITERATIONS,
        output_seed=OUTPUT_SEED,
        sim_max_decision_steps=SIM_MAX_DECISION_STEPS,
        verbose=VERBOSE,
        print_events=PRINT_EVENTS,
        print_artifacts=False,
    )
    outputs = [build_run_iteration_output(state) for state in result.states]
    _validate_outputs(outputs)

    print(f"\n=== offline multi-iteration validation: {len(outputs)} iterations ===", flush=True)
    for output in outputs:
        row = _build_summary_row(output.model_dump(mode="json"))
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if PRINT_JSON:
            print(json.dumps(output.model_dump(mode="json"), ensure_ascii=False, indent=2), flush=True)

    print("\nvalidation=passed", flush=True)


def _validate_outputs(outputs: list[Any]) -> None:
    if not outputs:
        raise ValueError("offline workflow did not produce any iteration output")

    failures: list[str] = []
    for output in outputs:
        if output.status != "completed":
            failures.append(f"iteration {output.iteration_index}: status={output.status!r}")
        if not output.iteration_tags:
            failures.append(f"iteration {output.iteration_index}: missing iteration_tags")
        if output.scheme is None:
            failures.append(f"iteration {output.iteration_index}: missing scheme")
            continue
        if not output.scheme.branch_executions:
            failures.append(f"iteration {output.iteration_index}: missing scheme.branch_executions")
        if not output.scheme.planned_agent_params:
            failures.append(f"iteration {output.iteration_index}: missing scheme.planned_agent_params")
        if not output.scheme.callback_params:
            failures.append(f"iteration {output.iteration_index}: missing scheme.callback_params")
        if not output.simulation_runs:
            failures.append(f"iteration {output.iteration_index}: missing simulation_runs")
        if output.overall_summary is None:
            failures.append(f"iteration {output.iteration_index}: missing overall_summary")

    if failures:
        raise ValueError("offline multi-iteration validation failed:\n" + "\n".join(failures))


def _build_summary_row(output: dict[str, Any]) -> dict[str, Any]:
    scheme = output.get("scheme") or {}
    branch_executions = scheme.get("branch_executions") or []
    simulation_runs = output.get("simulation_runs") or []
    first_simulation_result = (simulation_runs[0] or {}).get("simulation_result") if simulation_runs else {}
    metrics = (first_simulation_result or {}).get("metrics") or {}
    return {
        "iteration_index": output.get("iteration_index"),
        "status": output.get("status"),
        "tags": [item.get("label") for item in output.get("iteration_tags") or []],
        "branches": [
            {
                "branch_id": item.get("branch_id"),
                "agent_count": len(item.get("planned_agent_params") or []),
            }
            for item in branch_executions
        ],
        "agent_count": len(scheme.get("planned_agent_params") or []),
        "simulation_count": len(simulation_runs),
        "target_health_delta": metrics.get("target_health_delta"),
        "requested_weapon_count": metrics.get("requested_weapon_count"),
        "summary": (output.get("overall_summary") or {}).get("summary"),
    }


if __name__ == "__main__":
    main()
