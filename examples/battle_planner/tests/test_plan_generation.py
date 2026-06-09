from __future__ import annotations

import json

from battle_planner.config import LLMMode, config
from battle_planner.orchestration.nodes.agent_parameter_planning import (
    agent_parameter_planning_node,
)
from battle_planner.orchestration.nodes.agent_schema_loading import agent_schema_loading_node
from battle_planner.orchestration.state.state import build_initial_state
from battle_planner.workspace.local.demo_seed import build_local_task_run


def _render_human_input_lines(human) -> list[str]:
    lines = [
        f"- 目标: {human.goal}",
        f"- 风险偏好: {human.risk_style}",
    ]
    lines.extend(f"- 约束: {item}" for item in human.constraints)
    lines.extend(f"- 风险点: {item}" for item in human.risk_points)
    if human.notes:
        lines.append(f"- 业务备注: {human.notes}")
    return lines


def test_plan_generation(monkeypatch) -> None:
    monkeypatch.setattr(config.runtime, "llm_mode", LLMMode.OFFLINE)

    # 1. 业务侧导入 TaskPlan，并叠加人工输入生成 TaskContext/TaskRun。
    target_ids = ["red_CV16 “辽宁”号001型航空母舰_1"]
    air_unit_ids = ["blue_F/A-18F型“超级大黄蜂”战斗机_14"]
    naval_unit_ids = ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"]
    task_run = build_local_task_run()
    task_context = task_run.task_context
    branch_context = task_context.branches[0]

    # 2. 固定选择唯一分支，并把 TaskRun 信息整理成当前 agent node 可消费的输入。
    scenario_understanding_md = "\n".join(
        [
            "# 海上航母对抗想定理解",
            "",
            f"- plan_id: {task_context.plan_id}",
            f"- context_id: {task_context.context_id}",
            f"- run_id: {task_run.run_id}",
            f"- scenario_name: {task_context.scenario_name}",
            f"- side: {task_context.side}",
            f"- opponent_side: {task_context.opponent_side}",
            f"- goal: {task_context.human.goal}",
            "",
            "## 约束",
            *[f"- {item}" for item in task_context.human.constraints],
            "",
            "## 风险点",
            *[f"- {item}" for item in task_context.human.risk_points],
            "",
            "## 分支",
            *[f"- {item.name} ({item.branch_id}): {item.description}" for item in task_context.branches],
            "",
            "## 人工输入",
            *_render_human_input_lines(task_context.human),
        ]
    )
    battle_plan_md = "\n".join(
        [
            "# 测试作战方案",
            "",
            "## 目标",
            f"- {task_context.human.goal}",
            "",
            "## 分支配置",
            f"- {branch_context.name}",
            "",
            "## 人工补充",
            *_render_human_input_lines(branch_context.human),
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
    state = build_initial_state(task_run).model_copy(
        update={
            "iteration_index": 0,
            "scenario_understanding_md": scenario_understanding_md,
            "battle_plan_md": battle_plan_md,
        }
    )

    # 3. 调用现有 node：加载本地 tick-agent 说明，并生成 simulation node 的 agent 参数输入。
    state = agent_schema_loading_node(state)
    state = agent_parameter_planning_node(state)

    # 4. 验证 node 输出可以直接作为 simulation node 输入。
    planned_agent_params = [item.model_dump(mode="json") for item in state.planned_agent_params]
    simulation_node_input = {
        "scenario_name": state.scenario_name,
        "planned_agent_params": planned_agent_params,
    }
    payload = {
        "task_context": task_context.model_dump(mode="json", exclude_defaults=True),
        "task_run": task_run.model_dump(mode="json", exclude_defaults=True),
        "simulation_node_input": simulation_node_input,
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
    assert state.run_id == task_run.run_id
    assert state.context_id == task_context.context_id
    assert state.plan_id == task_context.plan_id
    assert simulation_node_input["scenario_name"] == task_context.scenario_name
    assert simulation_node_input["planned_agent_params"] == planned_agent_params


if __name__ == "__main__":
    test_plan_generation()
