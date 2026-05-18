from __future__ import annotations

from typing import Any

from battle_planner.adapters.scenario_loader import summarize_scenario
from battle_planner.data.demo_models import (
    AssetSummary,
    CapabilitySummary,
    MissionSchemaSummary,
    PlannerKnowledgePack,
    PlanningGoal,
)


def build_default_zc_planning_goal() -> PlanningGoal:
    return PlanningGoal(
        assumptions=[
            "已开发智能体包含空对海打击任务智能体。",
            "已开发智能体包含舰对海打击任务智能体。",
        ],
        scenario_assumptions=[
            "红方不进行主动防御。",
            "蓝方派出飞机执行空对海打击任务。",
            "蓝方使用舰载导弹打击红方目标。",
        ],
        objective="摧毁红方航母。",
        constraints=["必须在想定时间窗口内完成。"],
        optimization_objective="武器消耗最小。",
    )


def build_zc_lite_knowledge_pack(
    scenario_conf: dict[str, Any],
    *,
    planning_goal: PlanningGoal | None = None,
) -> PlannerKnowledgePack:
    goal = planning_goal or build_default_zc_planning_goal()
    scenario_summary = summarize_scenario(scenario_conf)
    asset_catalog = _build_asset_catalog(scenario_conf)
    weapon_catalog = _build_weapon_catalog(asset_catalog)
    mission_schema_catalog = _build_mission_schema_catalog()
    capability_catalog = _build_capability_catalog()

    return PlannerKnowledgePack(
        scenario_summary=scenario_summary,
        planning_goal=goal,
        force_summary=_build_force_summary(asset_catalog),
        asset_catalog=asset_catalog,
        weapon_catalog=weapon_catalog,
        capability_catalog=capability_catalog,
        mission_schema_catalog=mission_schema_catalog,
        planning_constraints=[
            *goal.assumptions,
            *goal.scenario_assumptions,
            *goal.constraints,
            f"优化目标：{goal.optimization_objective}",
        ],
        unknowns=[
            "首版未读取完整 pysim 原型数据库中的射程、命中率和毁伤字段。",
            "首版未通过环境 probe 验证每个 unit_id 与 target_id 的合法性。",
            "首版将红方防御行为固定为不主动变化。",
        ],
        evidence_refs={
            "scenario": "pythonlib/scenario/scenario_zc_lite.py",
            "mission_schema": "pythonlib/example_zc/mission/mission/mission.py",
            "capability_rules": "battle_planner.knowledge.pysim_provider static demo rules",
        },
    )


def render_knowledge_pack_md(knowledge_pack: PlannerKnowledgePack) -> str:
    goal = knowledge_pack.planning_goal
    lines = [
        f"# Planner Knowledge Pack：{knowledge_pack.scenario_summary.get('name')}",
        "",
        "## 规划目标",
        f"- 作战目标：{goal.objective}",
        f"- 优化目标：{goal.optimization_objective}",
        *[f"- 预先假设：{item}" for item in goal.assumptions],
        *[f"- 场景假设：{item}" for item in goal.scenario_assumptions],
        *[f"- 限制：{item}" for item in goal.constraints],
        "",
        "## 兵力摘要",
    ]
    for side, summary in knowledge_pack.force_summary.items():
        lines.append(
            f"- {side}: assets={summary['asset_count']}, weapons={summary['weapon_count']}, "
            f"aircraft_groups={summary['aircraft_group_count']}"
        )

    lines.extend(["", "## 关键资产"])
    for asset in knowledge_pack.asset_catalog[:8]:
        lines.append(
            f"- {asset.asset_id}: {asset.prototype} ({asset.side}), "
            f"position={asset.position}, weapons={len(asset.weapons)}, aircraft_groups={len(asset.aircrafts)}"
        )

    lines.extend(["", "## 可用能力"])
    for capability in knowledge_pack.capability_catalog:
        lines.append(
            f"- {capability.agent_name}: {capability.capability}, "
            f"subject={capability.subject}, target={capability.target}, action={capability.action_type}, "
            f"reason={capability.rationale}"
        )

    lines.extend(["", "## Mission Schema"])
    for schema in knowledge_pack.mission_schema_catalog:
        lines.append(
            f"- {schema.mission_type}: required={schema.required_fields}, optional={schema.optional_fields}, "
            f"example={schema.example}"
        )

    lines.extend(["", "## 未知项"])
    lines.extend(f"- {item}" for item in knowledge_pack.unknowns)
    return "\n".join(lines)


def _build_asset_catalog(scenario_conf: dict[str, Any]) -> list[AssetSummary]:
    assets: list[AssetSummary] = []
    for side, units in scenario_conf.get("units", {}).items():
        for index, unit in enumerate(units, start=1):
            prototype = str(unit.get("prototype", "unknown"))
            assets.append(
                AssetSummary(
                    side=side,
                    asset_id=f"{side}_{prototype}_{index}",
                    name=str(unit.get("name") or prototype),
                    prototype=prototype,
                    asset_type=_infer_asset_type(unit),
                    position=unit.get("position"),
                    weapons=list(unit.get("weapons", [])),
                    aircrafts=list(unit.get("aircrafts", [])),
                )
            )
    return assets


def _build_weapon_catalog(asset_catalog: list[AssetSummary]) -> list[dict[str, Any]]:
    weapon_catalog: list[dict[str, Any]] = []
    for asset in asset_catalog:
        for weapon in asset.weapons:
            weapon_catalog.append(
                {
                    "side": asset.side,
                    "platform": asset.asset_id,
                    "prototype": weapon.get("prototype"),
                    "num": weapon.get("num"),
                    "source": "platform_weapon",
                }
            )
        for aircraft_group in asset.aircrafts:
            for weapon in aircraft_group.get("weapons", []):
                weapon_catalog.append(
                    {
                        "side": asset.side,
                        "platform": asset.asset_id,
                        "aircraft": aircraft_group.get("name"),
                        "prototype": weapon.get("prototype"),
                        "num": weapon.get("num"),
                        "source": "aircraft_weapon",
                    }
                )
    return weapon_catalog


def _build_force_summary(asset_catalog: list[AssetSummary]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for asset in asset_catalog:
        side_summary = summary.setdefault(
            asset.side,
            {"asset_count": 0, "weapon_count": 0, "aircraft_group_count": 0},
        )
        side_summary["asset_count"] += 1
        side_summary["weapon_count"] += len(asset.weapons)
        side_summary["aircraft_group_count"] += len(asset.aircrafts)
    return summary


def _build_capability_catalog() -> list[CapabilitySummary]:
    return [
        CapabilitySummary(
            capability="空对海打击",
            agent_name="air_to_sea_strike_agent",
            subject="blue_F/A-18F型“超级大黄蜂”战斗机编组",
            target="red_CV16 “辽宁”号001型航空母舰_1",
            action_type="NavalAsuWStrike_Air",
            required_fields=["activation_time", "type", "unit_ids", "target_ids", "wp_nums"],
            rationale="蓝方航母搭载 F/A-18F 编组，想定中存在 AGM-154C 空对海武器。",
            confidence=0.7,
        ),
        CapabilitySummary(
            capability="舰对海打击",
            agent_name="naval_to_sea_strike_agent",
            subject="blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_2",
            target="red_CV16 “辽宁”号001型航空母舰_1",
            action_type="NavalAsuWStrike_Naval",
            required_fields=["activation_time", "type", "unit_ids", "target_ids", "wp_nums"],
            rationale="蓝方舰艇配置 RGM-109I 战斧巡航导弹，首版按可对海目标形成候选能力。",
            confidence=0.55,
        ),
    ]


def _build_mission_schema_catalog() -> list[MissionSchemaSummary]:
    return [
        MissionSchemaSummary(
            mission_type="NavalAsuWStrike_Air",
            description="空对海打击任务。",
            required_fields=["type", "unit_ids", "target_ids"],
            optional_fields=["activation_time", "wp_nums", "clear_targets", "attack_mode"],
            example={
                "activation_time": 120,
                "type": "NavalAsuWStrike_Air",
                "unit_ids": ["blue_F/A-18F型“超级大黄蜂”战斗机_14"],
                "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
                "wp_nums": [2],
            },
        ),
        MissionSchemaSummary(
            mission_type="NavalAsuWStrike_Naval",
            description="舰对海打击任务。",
            required_fields=["type", "unit_ids", "target_ids"],
            optional_fields=["activation_time", "wp_nums", "clear_targets"],
            example={
                "activation_time": 180,
                "type": "NavalAsuWStrike_Naval",
                "unit_ids": ["blue_DDG 104“斯特瑞特”导弹护卫舰[阿利伯克级IIA]_2"],
                "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
                "wp_nums": [2],
            },
        ),
    ]


def _infer_asset_type(unit: dict[str, Any]) -> str:
    prototype = str(unit.get("prototype", ""))
    if "CV" in prototype or "航母" in prototype or "航空母舰" in prototype:
        return "aircraft_carrier"
    if "DDG" in prototype or "驱逐舰" in prototype or "护卫舰" in prototype:
        return "surface_combatant"
    return "unknown"
