from __future__ import annotations

from battle_planner.data.demo_models import AgentParamSpec, FakeTickAgentSpec


def load_fake_tick_agent_specs() -> list[FakeTickAgentSpec]:
    return [
        FakeTickAgentSpec(
            name="strike_planner",
            description="生成对固定海上目标的空对海打击任务参数。",
            applicable_scenarios=["对手不主动变化", "围绕关键目标达成", "固定目标打击"],
            params=[
                AgentParamSpec(
                    name="unit_ids",
                    description="执行空对海打击的蓝方飞机 id 列表。",
                    type="list[str]",
                    default=[
                        "blue_F/A-18F型“超级大黄蜂”战斗机_14",
                        "blue_F/A-18F型“超级大黄蜂”战斗机_15",
                        "blue_F/A-18F型“超级大黄蜂”战斗机_16",
                        "blue_F/A-18F型“超级大黄蜂”战斗机_17",
                    ],
                ),
                AgentParamSpec(
                    name="target_ids",
                    description="需要打击的红方目标 id 列表。",
                    type="list[str]",
                    default=["red_CV16 “辽宁”号001型航空母舰_1"],
                ),
                AgentParamSpec(
                    name="weapon_per_target",
                    description="每个目标分配的武器数量。",
                    type="int",
                    default=4,
                    examples=[2, 4, 6],
                ),
            ],
        ),
        FakeTickAgentSpec(
            name="air_patrol_planner",
            description="生成空中巡逻或掩护任务参数，首版只用于给 LLM 理解能力边界。",
            applicable_scenarios=["目标区掩护", "固定航线巡逻", "打击前制空"],
            params=[
                AgentParamSpec(
                    name="reference_points",
                    description="巡逻参考点，经纬度列表。",
                    type="list[list[float]]",
                    default=[[16.0, 130.0]],
                ),
                AgentParamSpec(
                    name="patrol_radius_km",
                    description="巡逻半径，单位公里。",
                    type="float",
                    default=80.0,
                ),
            ],
        ),
        FakeTickAgentSpec(
            name="mission_timing_planner",
            description="生成任务启动时间和节奏参数。",
            applicable_scenarios=["多任务时序安排", "固定目标打击", "demo 参数生成"],
            params=[
                AgentParamSpec(
                    name="activation_time",
                    description="任务启动仿真时间，单位秒。",
                    type="int",
                    default=120,
                    examples=[60, 120, 300],
                ),
                AgentParamSpec(
                    name="max_decision_steps",
                    description="demo 执行的 DrillEnv 决策步数上限。",
                    type="int",
                    default=3,
                    examples=[1, 3, 5],
                ),
            ],
        ),
    ]
