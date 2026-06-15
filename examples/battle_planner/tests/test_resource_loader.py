from __future__ import annotations

import yaml
from battle_planner.keys import CONT
from battle_planner.workspace.resource.loader import (
    TICK_AGENT_ROOT,
    iter_callback_resources,
    iter_tick_agent_resources,
    load_callback_specs,
    load_tick_agent_specs,
    register_callback_resources,
    register_tick_agent_resources,
)

from forge.core.specs import (
    CallbackParams,
    CallbackSpec,
    ParamSpecTemplate,
    TickAgentParams,
)
from forge.registration import make_callback, make_tick_agent, registry


def test_tick_agent_resources_use_relative_entrypoints() -> None:
    """验证 tick-agent 资源使用相对入口声明。"""

    descriptors = iter_tick_agent_resources()

    assert {descriptor.name for descriptor in descriptors} == {
        "air_to_sea_strike_agent",
        "naval_to_sea_strike_agent",
    }
    assert all(descriptor.relative_entrypoint == "agent:Agent" for descriptor in descriptors)
    assert all(descriptor.resolved_entrypoint.startswith("battle_planner.") for descriptor in descriptors)


def test_load_tick_agent_specs_returns_resolved_entrypoints() -> None:
    """验证 tick-agent spec 能解析为可导入入口。"""

    specs = load_tick_agent_specs()

    assert {spec.name for spec in specs} == {"air_to_sea_strike_agent", "naval_to_sea_strike_agent"}
    assert all(spec.entrypoint.startswith("battle_planner.workspace.resource.") for spec in specs)


def test_tick_agent_config_preserves_param_key_and_display_name() -> None:
    """验证 config.yaml 中 name 是参数键，chineseName 还原为展示名。"""

    config = yaml.safe_load(
        (TICK_AGENT_ROOT / "air_to_sea_strike" / "config.yaml").read_text(encoding="utf-8")
    )
    start_time_param = next(param for param in config["PARAMS"] if param["name"] == "start_time")
    specs = load_tick_agent_specs()
    air_spec = next(spec for spec in specs if spec.name == "air_to_sea_strike_agent")

    assert start_time_param["name"] == "start_time"
    assert start_time_param["chineseName"] == "开始时间"
    assert air_spec.params["start_time"].name == "开始时间"
    assert air_spec.params["wp_num"].name == "武器数量"
    assert "chineseName" not in air_spec.params["start_time"].other


def test_register_tick_agent_resources_registers_makeable_agents() -> None:
    """验证 tick-agent 资源注册后可以实例化。"""

    registry.pop("tick_agent/air_to_sea_strike_agent", None)
    registry.pop("tick_agent/naval_to_sea_strike_agent", None)

    register_tick_agent_resources()

    agent = make_tick_agent(
        "air_to_sea_strike_agent",
        params=TickAgentParams(
            agent_name="air_to_sea_strike_agent",
            side="blue",
            params={
                "start_time": 0,
                "end_time": 1,
                "unit_ids": ["blue_air_1"],
                "target_ids": ["red_ship_1"],
            },
        ),
    )

    assert type(agent).__module__ == "battle_planner.workspace.resource.tick_agents.air_to_sea_strike.agent"
    assert agent.declaration.entrypoint == "agent:Agent"


def test_callback_resources_use_entrypoint_constant() -> None:
    """验证 callback 资源使用入口常量。"""

    descriptors = iter_callback_resources()

    assert {descriptor.name for descriptor in descriptors} == {"target_statistic"}
    assert descriptors[0].relative_entrypoint == "TargetStatistic"
    assert (
        descriptors[0].resolved_entrypoint
        == "battle_planner.workspace.resource.callbacks.target_statistic:TargetStatistic"
    )


def test_load_callback_specs_returns_resolved_entrypoints_and_shared_params() -> None:
    """验证 callback spec 能解析入口并复用参数声明。"""

    specs = load_callback_specs()
    target_spec = next(spec for spec in specs if spec.name == "target_statistic")

    assert target_spec.entrypoint.startswith("battle_planner.workspace.resource.")
    assert isinstance(target_spec.params["side"], ParamSpecTemplate)
    assert isinstance(target_spec.params["target_ids"], ParamSpecTemplate)
    assert target_spec.params["side"].name == "参演方"
    assert target_spec.params["target_ids"].name == "目标单位 ID 列表"
    assert target_spec.metrics["target_damage_ratio"].name == "目标毁伤比例"
    assert target_spec.metrics["target_damage_ratio"].other["agg"] is True
    assert "label" not in target_spec.metrics["target_damage_ratio"].other


def test_register_callback_resources_registers_makeable_callbacks() -> None:
    """验证 callback 资源注册后可以实例化。"""

    registry.pop("callback/target_statistic", None)

    register_callback_resources()

    callback = make_callback(
        "target_statistic",
        params=CallbackParams(
            name="target_statistic",
            callback_instance_id="target_statistic_test",
            params={"side": "red", "target_ids": ["red_target_1"]},
        ),
    )

    assert type(callback).__module__ == "battle_planner.workspace.resource.callbacks.target_statistic"
    assert isinstance(callback.declaration, CallbackSpec)


def test_callback_result_metrics_match_declared_metrics() -> None:
    """验证 callback 返回指标与声明指标保持一致。"""

    registry.pop("callback/target_statistic", None)
    register_callback_resources()
    callback = make_callback(
        "target_statistic",
        params=CallbackParams(
            name="target_statistic",
            callback_instance_id="target_statistic_test",
            params={"side": "red", "target_ids": ["red_target_1"]},
        ),
    )

    result = callback.result()

    assert set(result["metrics"]) == set(callback.declaration.metrics)
    assert "role" not in result
    assert "objective_achieved" not in result
    assert "completion_rate" not in result


def test_target_callback_returns_per_target_metrics() -> None:
    """验证目标统计 callback 返回目标级指标。"""

    target_id = "red_target_1"
    registry.pop("callback/target_statistic", None)
    register_callback_resources()
    callback = make_callback(
        "target_statistic",
        params=CallbackParams(
            name="target_statistic",
            callback_instance_id="target_statistic_test",
            params={"side": "red", "target_ids": [target_id]},
        ),
    )
    callback.observe(_target_observation(target_id, health=1000, health_percent=1.0))
    callback.observe(_target_observation(target_id, health=250, health_percent=0.25))

    result = callback.result()

    assert result["metrics"]["target_damage_ratio"] == {target_id: 0.75}


def _target_observation(target_id: str, *, health: int, health_percent: float) -> dict:
    return {
        "red": {},
        "sim_time": 0,
        CONT: {
            "state": {
                "red": {
                    target_id: {
                        "health": health,
                        "health_percent": health_percent,
                    }
                }
            }
        },
    }
