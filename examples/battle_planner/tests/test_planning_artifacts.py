from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

EXAMPLES_ROOT = Path(__file__).resolve().parents[2]
if str(EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_ROOT))


def _load_components() -> dict[str, Any]:
    from battle_planner.adapters.scenario_loader import load_zc_lite_scenario
    from battle_planner.knowledge import build_zc_lite_knowledge_pack
    from battle_planner.planning.base import AgentInputs
    from battle_planner.planning.battle_plan_generation import BattlePlanGenerationAgent
    from battle_planner.planning.scenario_understanding import ScenarioUnderstandingAgent
    from battle_planner.runtime.model_provider import OfflineModelProvider

    return {
        "AgentInputs": AgentInputs,
        "BattlePlanGenerationAgent": BattlePlanGenerationAgent,
        "OfflineModelProvider": OfflineModelProvider,
        "ScenarioUnderstandingAgent": ScenarioUnderstandingAgent,
        "build_zc_lite_knowledge_pack": build_zc_lite_knowledge_pack,
        "load_zc_lite_scenario": load_zc_lite_scenario,
    }


def test_scenario_understanding_artifact() -> None:
    components = _load_components()
    scenario_conf = components["load_zc_lite_scenario"]()
    knowledge_pack = components["build_zc_lite_knowledge_pack"](scenario_conf)

    result = components["ScenarioUnderstandingAgent"](
        model_provider=components["OfflineModelProvider"]()
    ).run(
        components["AgentInputs"](
            data={"knowledge_pack": knowledge_pack},
            skills=["理解想定并形成 Markdown 作战背景摘要"],
        )
    )

    print("\n\n===== scenario_understanding_md =====")
    print(result.output)
    print("===== end scenario_understanding_md =====\n")

    assert "摧毁红方航母" in result.output
    assert "空对海打击" in result.output
    assert result.trace.fallback_used is True


def test_battle_plan_generation_artifact() -> None:
    components = _load_components()
    scenario_conf = components["load_zc_lite_scenario"]()
    knowledge_pack = components["build_zc_lite_knowledge_pack"](scenario_conf)
    scenario_understanding = components["ScenarioUnderstandingAgent"](
        model_provider=components["OfflineModelProvider"]()
    ).run(components["AgentInputs"](data={"knowledge_pack": knowledge_pack}))

    result = components["BattlePlanGenerationAgent"](
        model_provider=components["OfflineModelProvider"]()
    ).run(
        components["AgentInputs"](
            data={
                "scenario_understanding_md": scenario_understanding.output,
                "knowledge_pack": knowledge_pack,
            },
            skills=["根据想定理解生成粗粒度作战方案"],
        )
    )

    print("\n\n===== battle_plan_md =====")
    print(result.output)
    print("===== end battle_plan_md =====\n")

    assert "模拟作战方案" in result.output
    assert "舰对海打击" in result.output
    assert "武器消耗" in result.output
    assert result.trace.fallback_used is True


if __name__ == '__main__':
    # test_scenario_understanding_artifact()
    test_battle_plan_generation_artifact()