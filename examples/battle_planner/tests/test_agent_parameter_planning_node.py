from __future__ import annotations

import importlib

from battle_planner.config import config
from battle_planner.orchestration.state.state import BattlePlannerState


def test_agent_parameter_planning_node_uses_display_preset(monkeypatch) -> None:
    node_module = importlib.import_module("battle_planner.orchestration.nodes.agent_parameter_planning")
    monkeypatch.setattr(config.workflow, "display_mode", True)

    def fail_build_model_provider():
        raise AssertionError("display mode should not build model provider")

    monkeypatch.setattr(node_module, "build_model_provider", fail_build_model_provider)

    state = BattlePlannerState(iteration_index=1)
    result = node_module.agent_parameter_planning_node(state)

    assert result.agent_param_source == "display_preset"
    assert result.planned_agent_params
