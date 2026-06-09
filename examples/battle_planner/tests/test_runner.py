"""测试 runner 运行并输出结构化 report。"""

from battle_planner.adapters.runtime.runner import Runner
from battle_planner.registry import register_battle_planner_modules

from forge.core.specs import CallbackParams, EnvLink, EnvMode, EnvParams, TickAgentParams

TARGET_CARRIER_ID = "red_CV16 “辽宁”号001型航空母舰_1"


def _make_air_strike_params(*, instance_id: str, params) -> TickAgentParams:
    template_params = {
        "start_time": 100,
        "end_time": 600,
        "unit_ids": ["blue_F/A-18F型“超级大黄蜂”战斗机_14"],
        "target_ids": [TARGET_CARRIER_ID],
        "wp_num": 2,
        "clear_targets": True,
    }
    template_params.update(params)
    return TickAgentParams(
        agent_instance_id=instance_id,
        agent_name="air_to_sea_strike_agent",
        side="blue",
        params=template_params,
    )


def _make_target_statistic_param(*, instance_id, params) -> CallbackParams:
    return CallbackParams(
        callback_instance_id=instance_id,
        name="target_statistic",
        params=params,
    )


def test_runner_simple() -> None:
    register_battle_planner_modules()
    env_params = EnvParams(
        name="pysim", mode=EnvMode.CREATE, link=EnvLink.GYM, params={"render_mode": "none"}
    )
    tick_agents = [
        _make_air_strike_params(
            instance_id="2175601143269425152",
            params={
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_15",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_14",
                ],
                "target_ids": [TARGET_CARRIER_ID],
            },
        ),
    ]
    callbacks = [
        _make_target_statistic_param(
            instance_id="2175601143269425153",
            params={"side": "red", "target_ids": [TARGET_CARRIER_ID]},
        )
    ]
    runner = Runner(
        env=env_params,
        tick_agents=tick_agents,
        callbacks=callbacks,
    )
    runner.reset()
    report = runner.run(max_step=5)

    assert report.env.env_name == "pysim"
    assert report.env.step_count > 0
    assert report.agents
    assert "2175601143269425153" in report.callbacks
