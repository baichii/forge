from __future__ import annotations

import json
from dataclasses import dataclass, field

from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState, build_initial_state
from battle_planner.orchestration.workflow_stream import WorkflowStreamService
from battle_planner.workspace.local.run_input_seed import build_local_task_run


@dataclass
class OfflineRunResult:
    states: list[BattlePlannerState] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)


def run_offline_iterations(
    *,
    max_iterations: int = 2,
    output_seed: str = "debug",
    sim_max_decision_steps: int | None = None,
    verbose: int = 2,
    print_events: bool = False,
    print_artifacts: bool = False,
) -> OfflineRunResult:
    original_llm_mode = settings.LLM_MODE
    original_output_seed = settings.OUTPUT_SEED
    original_sim_max_decision_steps = settings.SIM_MAX_DECISION_STEPS
    settings.LLM_MODE = LLMMode.OFFLINE
    settings.OUTPUT_SEED = output_seed
    settings.SIM_MAX_DECISION_STEPS = sim_max_decision_steps

    try:
        task_run = build_local_task_run()
        stream_service = WorkflowStreamService(workflow_name=task_run.options.workflow_name)
        result = OfflineRunResult()

        if print_events:
            print(f"\n=== offline workflow stream: {max_iterations} iterations ===", flush=True)

        for iteration_index in range(max_iterations):
            if print_events:
                print(f"\n--- iteration {iteration_index + 1} ---", flush=True)
            initial_state = build_initial_state(task_run).model_copy(
                update={
                    "iteration_index": iteration_index,
                    "history": list(result.history),
                    "verbose": verbose,
                }
            )
            stream_result = stream_service.stream(initial_state, print_events=print_events)
            state = stream_result.final_state
            result.states.append(state)
            if state.cur_stage == WorkflowStages.COMPLETE:
                result.history.append(build_history_item(state))
            if print_events:
                print(_iteration_summary(state), flush=True)

        if print_artifacts and result.states:
            print("\n=== iteration 1 artifacts ===", flush=True)
            print(json.dumps(artifact_snapshot(result.states[0]), ensure_ascii=False, indent=2), flush=True)
            print("\n=== iteration 1 run output ===", flush=True)
            print(
                json.dumps(
                    build_run_iteration_output(result.states[0]).model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )

        return result
    finally:
        settings.LLM_MODE = original_llm_mode
        settings.OUTPUT_SEED = original_output_seed
        settings.SIM_MAX_DECISION_STEPS = original_sim_max_decision_steps


def artifact_snapshot(state: BattlePlannerState) -> dict:
    return {
        "iteration_index": state.iteration_index,
        "scenario_name": state.scenario_name,
        "cur_stage": state.cur_stage,
        "agent_param_source": state.agent_param_source,
        "scenario_understanding_md": state.scenario_understanding_md,
        "battle_plan_md": state.battle_plan_md,
        "planned_branch_executions": [
            item.model_dump(mode="json") for item in state.planned_branch_executions
        ],
        "planned_agent_params": [item.model_dump(mode="json") for item in state.planned_agent_params],
        "simulation_results": [item.model_dump(mode="json") for item in state.simulation_results],
        "simulation_result": state.simulation_result.model_dump(mode="json")
        if state.simulation_result
        else None,
        "evaluation_reports": [item.model_dump(mode="json") for item in state.evaluation_reports],
        "evaluation_report": state.evaluation_report.model_dump(mode="json")
        if state.evaluation_report
        else None,
        "evaluation_summary": state.evaluation_summary.model_dump(mode="json")
        if state.evaluation_summary
        else None,
        "summary_evaluation": state.summary_evaluation.model_dump(mode="json")
        if state.summary_evaluation
        else None,
        "summary_md": state.summary_md,
    }


def _iteration_summary(state: BattlePlannerState) -> str:
    metrics = state.simulation_result.metrics if state.simulation_result else {}
    objective_achieved = state.evaluation_report.objective_achieved if state.evaluation_report else None
    return (
        f"iteration={state.iteration_index + 1} "
        f"stage={state.cur_stage} "
        f"sim_runs={len(state.simulation_results)} "
        f"mean_score={state.evaluation_summary.mean_score if state.evaluation_summary else None} "
        f"objective_achieved={objective_achieved} "
        f"target_health_delta={metrics.get('target_health_delta')} "
        f"requested_weapon_count={metrics.get('requested_weapon_count')}"
    )


def main() -> None:
    run_offline_iterations(max_iterations=2, print_events=True, print_artifacts=True)


if __name__ == "__main__":
    main()
