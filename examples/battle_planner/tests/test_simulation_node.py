from __future__ import annotations

from battle_planner.orchestration.nodes.simulation import _is_env_finished


def test_env_truncated_counts_as_finished() -> None:
    assert _is_env_finished("env_terminal") is True
    assert _is_env_finished("env_truncated") is True
    assert _is_env_finished("max_step") is False
