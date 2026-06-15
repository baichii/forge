from __future__ import annotations

from battle_planner.conf import LLMMode
from battle_planner.model import (
    EvaluationAggregateSpec,
    LLMTrace,
    SimulationRunResult,
    SummaryEvaluation,
)
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def test_summary_generation_node_accepts_missing_evaluation_report(monkeypatch) -> None:
    """验证总结节点不再要求硬编码 EvaluationReport。"""

    state = _make_state()

    result = _run_summary_generation_node(monkeypatch, state)

    assert result.evaluation_report is None
    assert result.summary_md.startswith("summary from fake")
    assert result.summary_evaluation.objective_achieved is True
    assert result.summary_evaluation.advice == "由 summary agent 输出。"
    assert result.cur_stage == WorkflowStages.COMPLETE


def test_summary_generation_node_passes_callback_reports_to_agent(monkeypatch) -> None:
    """验证总结节点把 runner report callback 原始结果传给 summary agent。"""

    captured: dict[str, object] = {}
    state = _make_state()

    result = _run_summary_generation_node(monkeypatch, state, captured=captured)

    assert result.cur_stage == WorkflowStages.COMPLETE
    assert "evaluation_report" not in captured
    assert captured["evaluation_summary"] == state.evaluation_summary
    assert captured["callback_reports"] == _runner_report()["callbacks"]


def _run_summary_generation_node(
    monkeypatch,
    state: BattlePlannerState,
    *,
    captured: dict[str, object] | None = None,
) -> BattlePlannerState:
    import battle_planner.orchestration.nodes.summary_generation as summary_module

    def fake_generate_summary(**kwargs):
        if captured is not None:
            captured.update(kwargs)
        return (
            "summary from fake",
            LLMTrace(node_name=WorkflowStages.SUMMARY_GENERATION),
            SummaryEvaluation(
                iteration_index=state.iteration_index,
                objective_achieved=True,
                advice="由 summary agent 输出。",
            ),
        )

    monkeypatch.setattr(summary_module.settings, "LLM_MODE", LLMMode.LIVE)
    monkeypatch.setattr(summary_module, "generate_summary", fake_generate_summary)
    return summary_module.summary_generation_node(state)


def _make_state() -> BattlePlannerState:
    return BattlePlannerState(
        iteration_index=1,
        scenario_understanding_md="红方航母为关键目标。",
        battle_plan_md="使用空中突击和海对海打击。",
        simulation_result=SimulationRunResult(
            steps=10,
            done=True,
            raw_summary={"runner_report": _runner_report()},
        ),
        evaluation_summary=EvaluationAggregateSpec(
            case_count=1,
            metric_summary={
                "target_damage_ratio": {
                    "key": "target_damage_ratio",
                    "name": "目标毁伤比例",
                    "description": "每个目标单位的毁伤比例。",
                    "mean": 1.0,
                    "min": 1.0,
                    "max": 1.0,
                    "std": 0.0,
                }
            },
        ),
    )


def _runner_report() -> dict:
    return {
        "callbacks": {
            "target_statistic_carrier": {
                "schema_version": "callback_eval.v0",
                "callback_instance_id": "target_statistic_carrier",
                "callback_name": "target_statistic",
                "metrics": {
                    "target_destroyed_count": 1,
                    "target_damage_ratio": {"target_a": 1.0},
                },
                "payload": {"targets": {"target_a": {"alive": False}}},
            }
        }
    }
