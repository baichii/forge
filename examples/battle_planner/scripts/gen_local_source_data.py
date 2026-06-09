"""生成用于本地运行的任务方案测试数据。"""

from battle_planner.model.source import TaskBranchSpec, TaskPlanSpec, TickAgentSourceSpec


def generate_local_task_plan() -> dict:
    """生成一个用于本地测试的 TaskPlan。"""

    plan_id = "2175313467819556864"
    branches = [
        TaskBranchSpec(
            branch_id="branch-carrier-strike-validation",
            name="空中突击与海对海打击",
            description="蓝方先组织空中突击压制红方航母，再使用海对海打击补充毁伤，目标是击沉对方航母。",
        )
    ]

    task_plan = TaskPlanSpec(
        plan_id=plan_id,
        name="海上航母对抗验证任务方案1",
        scenario_name="zc3_lite",
        side="blue",
        opponent_side="red",
        objective="在武器消耗受控的前提下压制并摧毁红方航母编队核心舰。",
        constraints=[
            "首轮验证聚焦一个主分支：空中突击、海对海打击，压制并摧毁对方航母。",
            "优先使用现有空对海和舰对海智能体能力，不扩展新能力类型。",
        ],
        branches=branches,
    )
    return task_plan.model_dump(mode="json")


def generate_local_tick_agents() -> list[dict]:
    """生成本地缓存的 tick-agents 数据信息，仅用于前端展示。"""

    from battle_planner.workspace.resource.loader import load_tick_agent_specs

    tick_agent_sources: list[dict] = []
    for tick_agent_spec in load_tick_agent_specs():
        source = TickAgentSourceSpec(
            tick_agent_id=tick_agent_spec.name,
            name=tick_agent_spec.name,
            description=tick_agent_spec.description,
            params={name: param.model_dump(mode="json") for name, param in tick_agent_spec.params.items()},
            version=tick_agent_spec.version,
        )
        tick_agent_sources.append(source.model_dump(mode="json"))
    return tick_agent_sources


if __name__ == "__main__":
    print(generate_local_task_plan())
    print(generate_local_tick_agents())
