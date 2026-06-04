from __future__ import annotations

import json

from battle_planner.config import config
from battle_planner.model.models import (
    DeductionSpec,
    StrategyParam,
)
from battle_planner.orchestration.nodes.agent_parameter_planning import (
    agent_parameter_planning_node,
)
from battle_planner.orchestration.nodes.agent_schema_loading import agent_schema_loading_node
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.loaders import load_scheme_config

from forge.core.specs import EnvLink, EnvMode


def test_plan_generation(monkeypatch) -> None:
    monkeypatch.setattr(config.workflow, "display_mode", True)

    # 1. 业务侧导入 scheme：首轮验证只保留一个策略分支。
    target_ids = ["red_CV16 “辽宁”号001型航空母舰_1"]
    air_unit_ids = ["blue_F/A-18F型“超级大黄蜂”战斗机_14"]
    naval_unit_ids = ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"]
    scheme = load_scheme_config("zc3_lite_carrier_validation")

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
        iteration_index=0,
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
                summary="单策略验证运行参数。",
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
    assert planned_agent_params
    assert deduction.strategy_params[0].agent_configs == planned_agent_params


if __name__ == "__main__":
    test_plan_generation()
