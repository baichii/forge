from __future__ import annotations

from typing import Any

from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState, build_initial_state
from battle_planner.orchestration.workflow_stream import WorkflowStreamService
from battle_planner.workspace.local.run_input_seed import build_local_task_run


def test_workflow_stream_service_streams_offline_workflow(monkeypatch) -> None:
    """验证 workflow stream 能跑通离线完整流程。"""

    _force_offline_workflow(monkeypatch)

    result = _stream_workflow(verbose=1)

    assert result.final_state.cur_stage == WorkflowStages.COMPLETE
    assert _stream_has_core_outputs(result)


def test_workflow_stream_service_respects_verbose_zero(monkeypatch) -> None:
    """验证 verbose=0 时不对外暴露日志事件。"""

    _force_offline_workflow(monkeypatch)

    result = _stream_workflow(verbose=0)

    assert result.final_state.cur_stage == WorkflowStages.COMPLETE
    assert not _log_events(result.custom_events) and _raw_log_events(result.events)


def test_workflow_stream_service_collects_verbose_two_messages(monkeypatch) -> None:
    """验证 verbose=2 时能收集节点内部消息。"""

    _force_offline_workflow(monkeypatch)

    result = _stream_workflow(verbose=2)
    assert any(event.get("phase") == EventPhases.MESSAGE for event in _log_events(result.custom_events))


def test_workflow_stream_service_prints_logs_when_enabled(monkeypatch, capsys) -> None:
    """验证 print_events 开启时能输出可读日志。"""

    _force_offline_workflow(monkeypatch)

    _stream_workflow(verbose=1, print_events=True)
    captured = capsys.readouterr()

    assert "[battle_planner][1][scenario_preparation][start]" in captured.out


def test_event_handler_is_safe_without_graph_writer() -> None:
    """验证非 graph 环境调用事件入口不会报错。"""

    event_handler(
        EventTypes.LOG,
        node="unit_test",
        phase=EventPhases.MESSAGE,
        level=EventLevels.NODE,
        payload={"state": BattlePlannerState(verbose=1)},
    )


def test_event_handler_dumps_model_payload(monkeypatch) -> None:
    """验证事件入口能序列化 Pydantic payload。"""

    captured: list[dict[str, Any]] = []

    def fake_get_stream_writer():
        return captured.append

    import langgraph.config as langgraph_config

    monkeypatch.setattr(langgraph_config, "get_stream_writer", fake_get_stream_writer)

    event_handler(
        EventTypes.LOG,
        node="unit_test",
        phase=EventPhases.MESSAGE,
        level=EventLevels.NODE,
        payload={"state": BattlePlannerState(verbose=1)},
    )

    assert captured[0]["payload"]["state"]["verbose"] == 1


def _stream_workflow(*, verbose: int, print_events: bool = False):
    task_run = build_local_task_run()
    initial_state = build_initial_state(task_run).model_copy(update={"verbose": verbose})
    stream_service = WorkflowStreamService(workflow_name=task_run.options.workflow_name)
    return stream_service.stream(initial_state, print_events=print_events)


def _force_offline_workflow(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_MODE", LLMMode.OFFLINE)
    monkeypatch.setattr(settings, "OUTPUT_SEED", "debug")
    monkeypatch.setattr(settings, "SIM_MAX_DECISION_STEPS", 70)


def _stream_has_core_outputs(result: Any) -> bool:
    event_pairs = {(event.get("node"), event.get("phase")) for event in _log_events(result.custom_events)}
    return bool(
        result.final_state.summary_md
        and result.final_state.planned_branch_executions
        and result.final_state.simulation_results
        and result.updates
        and (WorkflowStages.SCENARIO_PREPARATION, EventPhases.START) in event_pairs
        and (WorkflowStages.SUMMARY_GENERATION, EventPhases.END) in event_pairs
    )


def _log_events(events: list[Any]) -> list[dict[str, Any]]:
    return [
        event for event in events if isinstance(event, dict) and event.get("event_type") == EventTypes.LOG
    ]


def _raw_log_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_events = []
    for event in events:
        payload = event.get("payload")
        if (
            event.get("mode") == "custom"
            and isinstance(payload, dict)
            and payload.get("event_type") == EventTypes.LOG
        ):
            raw_events.append(payload)
    return raw_events
