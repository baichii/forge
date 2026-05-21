"""测试 runner 运行并输出结构化 report。"""

from battle_planner.adapters.runtime.runner import Runner
from battle_planner.registry import register_battle_planner_modules

from forge.core.specs import CallbackParams, EnvLink, EnvMode, EnvParams, TickAgentParams


def _make_air_strike_params(*, start_time: float, instance_id: str) -> TickAgentParams:
    return TickAgentParams(
        agent_instance_id=instance_id,
        agent_name="air_to_sea_strike_agent",
        side="blue",
        params={
            "start_time": start_time,
            "end_time": 600,
            "unit_ids": ["blue_F/A-18F型“超级大黄蜂”战斗机_14"],
            "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
            "wp_num": 2,
            "clear_targets": True,
        },
    )


class TestRunner:
    """验证同一想定下，任务下发与未下发时 report 的差异。"""

    def test_runner_report_with_dispatched_agent(self):
        register_battle_planner_modules()
        env_params = EnvParams(
            name="pysim", mode=EnvMode.CREATE, link=EnvLink.GYM, params={"render_mode": "none"}
        )
        tick_agent = _make_air_strike_params(start_time=300, instance_id="100")
        runner = Runner(
            env_params=env_params,
            tick_agents=[tick_agent],
            callbacks=[
                CallbackParams(
                    name="step_metric",
                    callback_instance_id="step_metric_primary",
                ),
                CallbackParams(
                    name="step_metric",
                    callback_instance_id="step_metric_secondary",
                ),
            ],
        )
        runner.reset()
        report = runner.run(max_step=None)
        assert "step_metric_primary" in report.callbacks
        assert "step_metric_secondary" in report.callbacks
        print("report: ", report)


if __name__ == "__main__":
    test_case = TestRunner()
    test_case.test_runner_report_with_dispatched_agent()
