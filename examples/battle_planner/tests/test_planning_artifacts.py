from __future__ import annotations

from typing import Any


def _load_components() -> dict[str, Any]:
    from battle_planner.adapters.runtime.scenario_loader import load_zc_lite_scenario
    from battle_planner.agents.base import AgentInputs
    from battle_planner.agents.battle_plan_generation import BattlePlanGenerationAgent
    from battle_planner.agents.context import build_zc_lite_knowledge_pack
    from battle_planner.agents.scenario_understanding import ScenarioUnderstandingAgent
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

    assert result.output


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

    assert result.output


if __name__ == "__main__":
    # test_scenario_understanding_artifact()
    test_battle_plan_generation_artifact()
