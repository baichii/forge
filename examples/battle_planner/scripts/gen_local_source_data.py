"""生成用于本地运行的任务方案测试数据。"""

import json

from battle_planner.model.source import TickAgentSourceSpec
from battle_planner.workspace.local.run_input_seed import build_local_task_plan


def generate_local_task_plan() -> dict:
    """生成一个用于本地测试的 TaskPlan。"""

    return build_local_task_plan().model_dump(mode="json")


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
    print(json.dumps(generate_local_task_plan(), ensure_ascii=False, indent=2))
    print(json.dumps(generate_local_tick_agents(), ensure_ascii=False, indent=2))
