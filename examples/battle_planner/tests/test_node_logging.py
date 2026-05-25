from __future__ import annotations

from battle_planner.orchestration.node_logging import _format_line


def test_node_logging_keeps_original_prefix_without_iteration() -> None:
    line = _format_line("simulation", "start", {"scenario": "zc3_lite"})

    assert line == "[battle_planner][simulation][start] scenario=zc3_lite"


def test_node_logging_formats_human_readable_iteration_prefix() -> None:
    first_line = _format_line("simulation", "start", {"iteration_index": 0})
    fifth_line = _format_line("simulation", "end", {"iteration_index": 4, "steps": 70})

    assert first_line == "[battle_planner][1][simulation][start]"
    assert fifth_line == "[battle_planner][5][simulation][end] steps=70"
    assert "iteration_index" not in fifth_line
