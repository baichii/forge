from __future__ import annotations

from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.scripts.run_offline import run_offline_iterations


def test_build_run_iteration_output_from_offline_workflow() -> None:
    """验证单轮 workflow state 能组装为输出模型。"""

    result = run_offline_iterations(
        max_iterations=1,
        sim_max_decision_steps=70,
        print_events=False,
        print_artifacts=False,
    )

    state = result.states[0]
    output = build_run_iteration_output(state)

    assert output.model_dump(mode="json")
    assert output.metric_aggregates
    assert output.simulation_runs[0].callback_reports
    assert "成功率" not in output.report_summary.summary
    assert "平均分" not in output.report_summary.summary
    assert "聚合指标" in output.report_summary.summary


def test_build_run_iteration_output_from_two_offline_iterations() -> None:
    """验证多轮 workflow state 都能组装为输出模型。"""

    result = run_offline_iterations(
        max_iterations=2,
        sim_max_decision_steps=70,
        print_events=False,
        print_artifacts=False,
    )

    outputs = [build_run_iteration_output(state) for state in result.states]

    assert len(outputs) == 2
    assert all(output.model_dump(mode="json") for output in outputs)
