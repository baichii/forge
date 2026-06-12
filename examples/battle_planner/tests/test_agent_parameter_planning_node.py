from __future__ import annotations

import importlib

from battle_planner.conf import LLMMode, settings
from battle_planner.orchestration.state.state import BattlePlannerState


def test_agent_parameter_planning_node_uses_run_output_seed(monkeypatch) -> None:
    """验证离线参数规划节点直接读取 run_output_seed。"""

    node_module = importlib.import_module("battle_planner.orchestration.nodes.agent_parameter_planning")
    monkeypatch.setattr(settings, "LLM_MODE", LLMMode.OFFLINE)

    def fail_build_model_provider():
        raise AssertionError("offline llm mode should not build model provider")

    monkeypatch.setattr(node_module, "build_model_provider", fail_build_model_provider)

    state = BattlePlannerState(iteration_index=1)
    result = node_module.agent_parameter_planning_node(state)

    assert result.agent_param_source == "run_output_seed"
    assert result.planned_agent_params
