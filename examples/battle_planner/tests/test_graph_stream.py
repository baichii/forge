from __future__ import annotations

from typing import Any

from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.orchestration.workflow_stream import (
    WorkflowStreamService,
    build_scenario_preparation_to_battle_plan_generation_graph,
    build_scenario_preparation_understanding_graph,
)
from battle_planner.workspace.local.run_output_seed import (
    DEBUG_SCENARIO_UNDERSTANDING_MD,
    load_battle_plan_generation_output_seed,
)


def test_workflow_stream_service_streams_scenario_preparation_slice(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    def fail_understand_scenario(*args, **kwargs):
        raise AssertionError("offline graph stream should use run_output_seed")

    import battle_planner.orchestration.nodes.scenario_understanding as scenario_module

    monkeypatch.setattr(scenario_module, "understand_scenario", fail_understand_scenario)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    result = stream_service.stream(BattlePlannerState())

    assert result.final_state.cur_stage == WorkflowStages.SCENARIO_UNDERSTANDING
    assert result.final_state.scenario_name == "zc3_lite"
    assert result.final_state.scenario_understanding_md == DEBUG_SCENARIO_UNDERSTANDING_MD
    assert result.final_state.llm_traces[-1].node_name == WorkflowStages.SCENARIO_UNDERSTANDING


def test_workflow_stream_service_streams_battle_plan_seed_slice(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    def fail_generate_battle_plan(*args, **kwargs):
        raise AssertionError("offline graph stream should use battle_plan_generation run_output_seed")

    import battle_planner.orchestration.nodes.battle_plan_generation as battle_plan_module

    monkeypatch.setattr(battle_plan_module, "generate_battle_plan", fail_generate_battle_plan)

    stream_service = WorkflowStreamService(
        graph=build_scenario_preparation_to_battle_plan_generation_graph()
    )
    result = stream_service.stream(BattlePlannerState(iteration_index=6, verbose=2))
    seed = load_battle_plan_generation_output_seed(iteration_index=6)

    assert result.final_state.cur_stage == WorkflowStages.BATTLE_PLAN_GENERATION
    assert result.final_state.battle_plan_md == seed.battle_plan_md
    assert result.final_state.llm_traces[-1].parsed_output["trace_summary"]["seed_iteration_index"] == 1


def test_workflow_stream_service_collects_custom_node_events(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    result = stream_service.stream(BattlePlannerState(iteration_index=1, verbose=1))
    node_events = [event for event in result.custom_events if event.get("event_type") == EventTypes.LOG]
    event_pairs = {(event.get("node"), event.get("phase")) for event in node_events}

    assert (WorkflowStages.SCENARIO_PREPARATION, "start") in event_pairs
    assert (WorkflowStages.SCENARIO_PREPARATION, "end") in event_pairs
    assert (WorkflowStages.SCENARIO_UNDERSTANDING, "start") in event_pairs
    assert (WorkflowStages.SCENARIO_UNDERSTANDING, "end") in event_pairs
    assert (WorkflowStages.SCENARIO_UNDERSTANDING, "message") not in event_pairs
    assert all(event.get("iteration_index") == 1 for event in node_events)
    assert all(event.get("event_type") == EventTypes.LOG for event in node_events)


def test_workflow_stream_service_collects_verbose_two_messages(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    result = stream_service.stream(BattlePlannerState(verbose=2))
    node_messages = [
        event
        for event in result.custom_events
        if event.get("event_type") == EventTypes.LOG and event.get("phase") == EventPhases.MESSAGE
    ]

    assert node_messages
    assert node_messages[0]["payload"]["source"] == "run_output_seed"


def test_workflow_stream_service_collects_updates(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    result = stream_service.stream(BattlePlannerState())
    update_nodes = set()
    for update in result.updates:
        update_nodes.update(_update_node_names(update))

    assert WorkflowStages.SCENARIO_PREPARATION in update_nodes
    assert WorkflowStages.SCENARIO_UNDERSTANDING in update_nodes
    assert result.final_state.scenario_understanding_md == DEBUG_SCENARIO_UNDERSTANDING_MD


def test_workflow_stream_service_respects_verbose_zero(monkeypatch) -> None:
    _force_offline_output_seed(monkeypatch)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    result = stream_service.stream(BattlePlannerState(verbose=0))
    node_events = [event for event in result.custom_events if event.get("event_type") == EventTypes.LOG]
    raw_log_events = [
        event["payload"]
        for event in result.events
        if event.get("mode") == "custom"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("event_type") == EventTypes.LOG
    ]

    assert node_events == []
    assert raw_log_events
    assert result.final_state.scenario_understanding_md == DEBUG_SCENARIO_UNDERSTANDING_MD


def test_workflow_stream_service_prints_logs_when_enabled(monkeypatch, capsys) -> None:
    _force_offline_output_seed(monkeypatch)

    stream_service = WorkflowStreamService(graph=build_scenario_preparation_understanding_graph())
    stream_service.stream(BattlePlannerState(verbose=1), print_events=True)
    captured = capsys.readouterr()

    assert "[battle_planner][1][scenario_preparation][start]" in captured.out
    assert "[battle_planner][1][scenario_understanding][end]" in captured.out


def test_event_handler_is_safe_without_graph_writer() -> None:
    event_handler(
        EventTypes.LOG,
        node="unit_test",
        phase=EventPhases.MESSAGE,
        level=EventLevels.NODE,
        payload={"state": BattlePlannerState(verbose=1)},
    )


def test_event_handler_dumps_model_payload(monkeypatch) -> None:
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


def _force_offline_output_seed(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_MODE", LLMMode.OFFLINE)
    monkeypatch.setattr(settings, "OUTPUT_SEED", "debug")


def _update_node_names(update: Any) -> set[str]:
    if not isinstance(update, dict):
        return set()
    return set(update)
