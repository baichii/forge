"""离线 workflow 运行入口。

Notes:
    LLM 产物读取 run_output_seed，仿真和评估仍走真实链路。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState, build_initial_state
from battle_planner.orchestration.workflow_stream import WorkflowStreamService
from battle_planner.utils.run_store import LocalRunStore
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

    task_run = None
    run_store = None
    result = OfflineRunResult()
    try:
        task_run = build_local_task_run()
        stream_service = WorkflowStreamService(workflow_name=task_run.options.workflow_name)
        run_store = LocalRunStore() if settings.should_store_artifacts else None
        if run_store is not None:
            run_store.write_run_info(task_run=task_run)

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
            if run_store is not None:
                run_store.write_iteration_output(
                    run_id=task_run.run_id,
                    output=build_run_iteration_output(state),
                )
            if state.cur_stage == WorkflowStages.COMPLETE:
                result.history.append(build_history_item(state))
            if print_events:
                print(_iteration_summary(state), flush=True)

        if run_store is not None:
            error_states = [state for state in result.states if state.error]
            if error_states:
                run_store.mark_run_failed(
                    run_id=task_run.run_id,
                    reason="workflow_state_error",
                    message=error_states[-1].error or "",
                    last_iteration_index=error_states[-1].iteration_index,
                )
            else:
                run_store.mark_run_completed(
                    run_id=task_run.run_id,
                    iteration_count=len(result.states),
                )

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
    except Exception as exc:
        if run_store is not None and task_run is not None:
            last_iteration_index = result.states[-1].iteration_index if result.states else None
            run_store.mark_run_failed(
                run_id=task_run.run_id,
                reason="workflow_exception",
                message=str(exc),
                last_iteration_index=last_iteration_index,
            )
        raise
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
    objective_achieved = state.summary_evaluation.objective_achieved if state.summary_evaluation else None
    metric_count = len(state.evaluation_summary.metric_summary) if state.evaluation_summary else None
    return (
        f"iteration={state.iteration_index + 1} "
        f"stage={state.cur_stage} "
        f"sim_runs={len(state.simulation_results)} "
        f"metric_count={metric_count} "
        f"objective_achieved={objective_achieved} "
        f"target_damage_ratio={metrics.get('target_damage_ratio')}"
    )


def main() -> None:
    run_offline_iterations(max_iterations=2, print_events=True, print_artifacts=True)


if __name__ == "__main__":
    main()
