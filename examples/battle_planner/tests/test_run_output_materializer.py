from __future__ import annotations

from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.scripts.run_offline import run_offline_iterations


def test_build_run_iteration_output_from_offline_workflow() -> None:
    result = run_offline_iterations(
        max_iterations=1,
        sim_max_decision_steps=70,
        print_events=False,
        print_artifacts=False,
    )

    state = result.states[0]
    output = build_run_iteration_output(state)
    dumped = output.model_dump(mode="json")

    assert state.cur_stage == WorkflowStages.COMPLETE
    assert dumped["status"] == "completed"
    assert dumped["iteration_tags"]
    assert [item["branch_id"] for item in dumped["scheme"]["branch_executions"]] == [1, 2]


def test_build_run_iteration_output_from_two_offline_iterations() -> None:
    result = run_offline_iterations(
        max_iterations=2,
        sim_max_decision_steps=70,
        print_events=False,
        print_artifacts=False,
    )

    outputs = [build_run_iteration_output(state).model_dump(mode="json") for state in result.states]

    assert len(outputs) == 2
    assert all(output["iteration_tags"] for output in outputs)
    assert all(
        [item["branch_id"] for item in output["scheme"]["branch_executions"]] == [1, 2]
        for output in outputs
    )
