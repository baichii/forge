"""生成用于本地运行的测试数据"""

from battle_planner.conf import Settings
from battle_planner.model.source import SchemeSourceSpec, StrategySourceSpec, TickAgentSourceSpec
from battle_planner.utils.snowflake import snowflake


def generate_local_scheme() -> dict:
    """生成一个用于本地测试的scheme"""

    # scheme_id = snowflake.generate()
    scheme_id = 2175313467819556864

    strategies_source = [
        StrategySourceSpec(
            strategy_id=1,
            name="空中突击与海对海打击",
            description="蓝方先组织空中突击压制红方航母，再使用海对海打击补充毁伤，目标是击沉对方航母。",
        )
    ]

    scheme_source = SchemeSourceSpec(
        scheme_id=scheme_id,
        name="海上航母对抗验证方案1",
        scenario_name="zc3_lite",
        side="blue",
        opponent_side="red",
        strategies=strategies_source,
    )

    return scheme_source.model_dump()


def generate_tick_agents() -> list:
    """生成本地缓存的tick-agents的数据信息，仅用于前端展示"""
    from battle_planner.workspace.resource.loader import load_tick_agent_specs

    tick_agent_specs = load_tick_agent_specs()
    tick_agent_sources = []

    for tick_agent_spec in tick_agent_specs:
        tick_agent_sources.append(tick_agent_spec.model_dump())

    return tick_agent_sources


if __name__ == "__main__":
    generate_local_scheme()
    generate_tick_agents()
