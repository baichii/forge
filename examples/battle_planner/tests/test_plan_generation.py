from __future__ import annotations

import json

from battle_planner.config import LLMMode, config
from battle_planner.model.models import (
    HumanInputSpec,
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
    build_task_context,
    build_task_run,
)
from battle_planner.orchestration.nodes.agent_parameter_planning import (
    agent_parameter_planning_node,
)
from battle_planner.orchestration.nodes.agent_schema_loading import agent_schema_loading_node
from battle_planner.orchestration.state.state import build_initial_state
from battle_planner.workspace.local.loaders import load_task_plan_config


def test_plan_generation(monkeypatch) -> None:
    monkeypatch.setattr(config.runtime, "llm_mode", LLMMode.OFFLINE)

    # 1. 业务侧导入 TaskPlan，并叠加人工输入生成 TaskContext/TaskRun。
    target_ids = ["red_CV16 “辽宁”号001型航空母舰_1"]
    air_unit_ids = ["blue_F/A-18F型“超级大黄蜂”战斗机_14"]
    naval_unit_ids = ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_1"]
    task_plan = load_task_plan_config("zc3_lite_carrier_validation")
    branch = task_plan.branches[0]
    task_context_request = TaskContextCreateRequest(
        plan_id=task_plan.plan_id,
        name="航母对抗任务上下文001",
        plan_human=HumanInputSpec(
            summary="人工希望先验证任务方案、策略迭代和推演配置的数据链路。",
            items=[
                "当前只保留一个策略分支，不考虑备选方案对比。",
                "只评价该策略是否完成摧毁航母目标。",
            ],
        ),
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id=branch.branch_id,
                human=HumanInputSpec(
                    summary="人工确认本轮只做单分支验证。",
                    items=[
                        "不要同时优化对手策略。",
                        "武器数量先保守，后续根据仿真反馈调整。",
                    ],
                ),
            )
        ],
    )
    task_context = build_task_context(
        task_plan,
        task_context_request,
        task_context_id="task-context-test-001",
        created_at="2026-06-09 00:00:00",
    )
    task_run = build_task_run(
        task_context,
        TaskRunCreateRequest(
            task_context_id=task_context.task_context_id,
            run_name="航母对抗策略迭代运行001",
            options={
                "workflow_name": "zc_lite_baseline",
                "max_iterations": 5,
                "sim_runs_per_scheme": 1,
                "max_retry": 1,
            },
        ),
        run_id="task-run-test-001",
        created_at="2026-06-09 00:00:00",
    )

    # 2. 固定选择唯一分支，并把 TaskRun 信息整理成当前 agent node 可消费的输入。
    branch_human = task_context.branch_humans[0].human
    platform_summary = str(branch.platform.get("summary") or "")
    platform_items = branch.platform.get("items") if isinstance(branch.platform.get("items"), list) else []
    scenario_understanding_md = "\n".join(
        [
            "# 海上航母对抗想定理解",
            "",
            f"- plan_id: {task_plan.plan_id}",
            f"- task_context_id: {task_context.task_context_id}",
            f"- run_id: {task_run.run_id}",
            f"- scenario_name: {task_plan.scenario_name}",
            f"- side: {task_plan.side}",
            f"- opponent_side: {task_plan.opponent_side}",
            f"- objective: {task_plan.objective}",
            "",
            "## 约束",
            *[f"- {item}" for item in task_plan.constraints],
            "",
            "## 分支",
            *[f"- {item.name} ({item.branch_id}): {item.description}" for item in task_plan.branches],
            "",
            "## 人工输入",
            f"- {task_context.plan_human.summary}",
            *[f"- {item}" for item in task_context.plan_human.items],
        ]
    )
    battle_plan_md = "\n".join(
        [
            "# 测试作战方案",
            "",
            "## 目标",
            f"- {task_plan.objective}",
            "",
            "## 上游平台打法",
            f"- {platform_summary}",
            *[f"- {item}" for item in platform_items],
            "",
            "## 人工补充",
            f"- {branch_human.summary}",
            *[f"- {item}" for item in branch_human.items],
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
        "task_plan": task_plan.model_dump(mode="json", exclude_defaults=True),
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
    assert state.task_context_id == task_context.task_context_id
    assert state.plan_id == task_plan.plan_id
    assert simulation_node_input["scenario_name"] == task_plan.scenario_name
    assert simulation_node_input["planned_agent_params"] == planned_agent_params


if __name__ == "__main__":
    test_plan_generation()
