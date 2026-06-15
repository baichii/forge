from __future__ import annotations

import importlib

from battle_planner.agents.agent_parameter_planning import plan_branch_executions
from battle_planner.conf import LLMMode, settings
from battle_planner.llm_runtime.model_provider import ModelResponse
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
    assert result.planned_branch_executions
    assert result.planned_agent_params
    assert result.planned_agent_params == [
        agent
        for branch_execution in result.planned_branch_executions
        for agent in branch_execution.planned_agent_params
    ]


def test_plan_branch_executions_parses_branch_level_contract() -> None:
    """验证 live agent 参数规划合同按分支返回执行参数。"""

    branch_executions, trace = plan_branch_executions(
        scenario_understanding_md="scenario",
        battle_plan_md="plan",
        agent_specs=[],
        branch_contexts=[{"branch_id": 1, "name": "branch"}],
        model_provider=FakeBranchExecutionProvider(),
    )

    assert trace.fallback_used is False
    assert len(branch_executions) == 1
    assert branch_executions[0].branch_id == 1
    assert branch_executions[0].planned_agent_params[0].agent_name == "air_to_sea_strike_agent"


class FakeBranchExecutionProvider:
    name = "fake"

    def complete(self, request):
        return ModelResponse(
            content=(
                '{"branch_executions":[{"branch_id":1,"planned_agent_params":['
                '{"agent_instance_id":"air_001","agent_name":"air_to_sea_strike_agent",'
                '"side":"blue","params":{"unit_ids":["blue_air_1"],"target_ids":["red_ship_1"]}}'
                "]}]}"
            ),
            provider=self.name,
        )
