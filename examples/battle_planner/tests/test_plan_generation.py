from __future__ import annotations

import json

from battle_planner.data.models import (
    DeductionSpec,
    HumanInputSpec,
    PlatformTacticSpec,
    SchemeSpec,
    StrategyParam,
    StrategySpec,
)
from battle_planner.orchestration.nodes.agent_parameter_planning import (
    agent_parameter_planning_node,
)
from battle_planner.orchestration.nodes.agent_schema_loading import agent_schema_loading_node
from battle_planner.orchestration.state.state import BattlePlannerState

from forge.core.specs import EnvLink, EnvMode


def test_plan_generation() -> None:
    # 1. 业务侧导入 scheme：稻草人测试只保留一个 StrategySpec。
    target_ids = ["red_CV16 “辽宁”号001型航空母舰_1"]
    air_unit_ids = ["blue_F/A-18F型“超级大黄蜂”战斗机_14"]
    naval_unit_ids = ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"]
    strategy_id = "strategy-carrier-strawman"
    scheme = SchemeSpec(
        scheme_id="10001",
        name="海上航母对抗稻草人测试方案",
        scenario_name="zc3_lite",
        side="blue",
        opponent_side="red",
        objective="在武器消耗受控的前提下压制并摧毁红方航母编队核心舰。",
        constraints=[
            "稻草人测试只验证一个策略：空中突击、海对海打击，击沉对方航母。",
            "优先使用现有空对海和舰对海 tick-agent schema，不扩展新 agent 类型。",
            "默认红方不主动变化，先生成可进入 simulation node 的运行参数。",
        ],
        human=HumanInputSpec(
            summary="人工希望先验证 scheme -> strategy -> deduction 的数据链路。",
            items=[
                "当前只保留一个 StrategySpec，不考虑备选方案对比。",
                "callback 只评价该策略是否完成摧毁航母目标。",
            ],
        ),
        strategies=[
            StrategySpec(
                strategy_id=strategy_id,
                name="空中突击与海对海打击",
                description="蓝方先组织空中突击压制红方航母，再使用海对海打击补充毁伤，目标是击沉对方航母。",
                platform=PlatformTacticSpec(
                    summary="上游平台建议采用空中突击和海对海打击协同压制红方航母。",
                    items=[
                        "空中编队在 120 秒后进入攻击窗口。",
                        "舰艇编队在空袭后补充打击同一航母目标。",
                        "目标是击沉红方航母。",
                    ],
                ),
                human=HumanInputSpec(
                    summary="人工确认本轮只做单策略稻草人测试。",
                    items=[
                        "不要同时优化对手策略。",
                        "武器数量先保守，后续根据仿真反馈调整。",
                    ],
                ),
            ),
        ],
    )

    # 2. 固定选择唯一策略，并把 scheme 信息整理成当前 agent node 可消费的输入。
    strategy = scheme.strategies[0]
    scenario_understanding_md = "\n".join(
        [
            "# 海上航母对抗想定理解",
            "",
            f"- scheme_id: {scheme.scheme_id}",
            f"- scenario_name: {scheme.scenario_name}",
            f"- side: {scheme.side}",
            f"- opponent_side: {scheme.opponent_side}",
            f"- objective: {scheme.objective}",
            "",
            "## 约束",
            *[f"- {item}" for item in scheme.constraints],
            "",
            "## 策略",
            *[
                f"- {strategy.name} ({strategy.strategy_id}): {strategy.description}"
                for strategy in scheme.strategies
            ],
            "",
            "## 人工输入",
            f"- {scheme.human.summary}",
            *[f"- {item}" for item in scheme.human.items],
        ]
    )
    battle_plan_md = "\n".join(
        [
            "# 测试作战方案",
            "",
            "## 目标",
            f"- {scheme.objective}",
            "",
            "## 上游平台打法",
            f"- {strategy.platform.summary}",
            *[f"- {item}" for item in strategy.platform.items],
            "",
            "## 人工补充",
            f"- {strategy.human.summary}",
            *[f"- {item}" for item in strategy.human.items],
            "",
            "## 参数生成提示",
            json.dumps(
                {
                    "target_ids": target_ids,
                    "agent_unit_ids": {
                        "air_to_sea_strike_agent": air_unit_ids,
                        "naval_to_sea_strike_agent": naval_unit_ids,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            "- 必须逐字符复制上面 JSON 中的具体 unit_ids 和 target_ids，不要生成占位 id。",
            "- 使用 air_to_sea_strike_agent 和 naval_to_sea_strike_agent。",
            "- 输出必须能作为 simulation node 的 planned_agent_params。",
        ]
    )
    state = BattlePlannerState(
        scenario_name=scheme.scenario_name,
        scenario_understanding_md=scenario_understanding_md,
        battle_plan_md=battle_plan_md,
    )

    # 3. 调用现有 node：加载本地 tick-agent 说明，并生成 simulation node 的 agent 参数输入。
    state = agent_schema_loading_node(state)
    state = agent_parameter_planning_node(state)

    # 4. 按当前 spec/params 设计，把 node 输出包装成 deduction，便于查看 strategy runtime 配置。
    planned_agent_params = [item.model_dump(mode="json") for item in state.planned_agent_params]
    deduction = DeductionSpec(
        deduction_id="deduction-carrier-battle-001",
        scheme_id=scheme.scheme_id,
        status="ready_for_simulation",
        summary="测试 scheme 已通过参数规划节点生成 simulation node 输入。",
        env_config={
            "name": "pysim",
            "mode": EnvMode.CREATE,
            "link": EnvLink.GYM,
            "params": {
                "scenario_name": scheme.scenario_name,
                "render_mode": "none",
            },
        },
        strategy_params=[
            StrategyParam(
                strategy_id=strategy.strategy_id,
                status="ready_for_simulation",
                summary="单策略稻草人测试运行参数。",
                agent_configs=planned_agent_params,
                callback_configs=[
                    {
                        "name": "target_statistic",
                        "callback_instance_id": "target_statistic_carrier",
                        "params": {
                            "side": scheme.opponent_side,
                            "target_ids": target_ids,
                        },
                    }
                ],
            )
        ],
    )

    # 5. 打印完整 payload：重点看 deduction 和 simulation_node_input。
    payload = {
        "scheme": scheme.model_dump(mode="json", exclude_defaults=True),
        "deduction": deduction.model_dump(mode="json", exclude_defaults=True),
        "simulation_node_input": {
            "scenario_name": state.scenario_name,
            "planned_agent_params": planned_agent_params,
        },
        "node_trace_summary": [
            {
                "node_name": trace.node_name,
                "fallback_used": trace.fallback_used,
                "error": trace.error,
            }
            for trace in state.llm_traces
        ],
    }
    print("\n\n===== test_plan_generation_node_simulation_input =====")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("===== end_test_plan_generation_node_simulation_input =====\n")


if __name__ == "__main__":
    test_plan_generation()
