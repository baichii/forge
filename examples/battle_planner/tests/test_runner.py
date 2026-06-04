"""测试 runner 运行并输出结构化 report。"""

import os

import pytest
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


def _make_naval_strike_params(*, instance_id: str, params) -> TickAgentParams:
    template_params = {
        "start_time": 100,
        "end_time": 1200,
        "unit_ids": ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"],
        "target_ids": [TARGET_CARRIER_ID],
        "wp_num": 4,
        "clear_targets": True,
    }
    template_params.update(params)
    return TickAgentParams(
        agent_instance_id=instance_id,
        agent_name="naval_to_sea_strike_agent",
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
            instance_id="10001",
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
            instance_id="20001",
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
    assert "20001" in report.callbacks


@pytest.mark.skipif(
    os.getenv("BATTLE_PLANNER_RUN_HARD_RUNNER_TEST", "").strip().lower() not in {"1", "true", "yes", "on"},
    reason="set BATTLE_PLANNER_RUN_HARD_RUNNER_TEST=true to run the long pysim hard runner",
)
def test_runner_hard() -> None:
    register_battle_planner_modules()
    env_params = EnvParams(
        name="pysim", mode=EnvMode.CREATE, link=EnvLink.GYM, params={"render_mode": "none"}
    )
    tick_agents = [
        _make_air_strike_params(
            instance_id="air_hard_01",
            params={
                "end_time": 1200,
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_11",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_12",
                ],
                "wp_num": 4,
            },
        ),
        _make_air_strike_params(
            instance_id="air_hard_02",
            params={
                "end_time": 1200,
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_13",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_14",
                ],
                "wp_num": 4,
            },
        ),
        _make_air_strike_params(
            instance_id="air_hard_03",
            params={
                "end_time": 1200,
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_15",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_16",
                ],
                "wp_num": 4,
            },
        ),
        _make_air_strike_params(
            instance_id="air_hard_04",
            params={
                "end_time": 1200,
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_17",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_18",
                ],
                "wp_num": 4,
            },
        ),
        _make_air_strike_params(
            instance_id="air_hard_05",
            params={
                "end_time": 1200,
                "unit_ids": [
                    "blue_F/A-18F型“超级大黄蜂”战斗机_19",
                    "blue_F/A-18F型“超级大黄蜂”战斗机_20",
                ],
                "wp_num": 4,
            },
        ),
        _make_naval_strike_params(
            instance_id="naval_hard_01",
            params={
                "unit_ids": ["blue_CVN 68“尼米兹号”尼米兹级核动力航空母舰_1"],
                "wp_num": 8,
            },
        ),
        _make_naval_strike_params(
            instance_id="naval_hard_02",
            params={
                "unit_ids": ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"],
                "wp_num": 10,
            },
        ),
    ]
    callbacks = [
        _make_target_statistic_param(
            instance_id="target_statistic_hard",
            params={"side": "red", "target_ids": [TARGET_CARRIER_ID]},
        )
    ]
    runner = Runner(
        env=env_params,
        tick_agents=tick_agents,
        callbacks=callbacks,
    )
    runner.reset()
    report = runner.run(max_step=None)
    target_report = report.callbacks["target_statistic_hard"][TARGET_CARRIER_ID]
    assert target_report["alive"] is False
    print("hard report: ", report)


if __name__ == "__main__":
    test_runner_hard()
