"""把一个极简 pysim observation 投影成本体事实的开发示例。

这个文件刻意写得偏具体：它代表未来某个 pysim adapter 包里的内容，
而不是 ``forge.core`` 里应该内置的通用逻辑。

这里要演示的是数据流和稀疏属性：

1. pysim 每帧给出环境原始态势，例如 ``blue_fighter_1.health = 96``。
2. adapter 把环境 ID 映射成稳定的 ontology object_id。
3. adapter 把 ``side``、``health``、``position`` 等字段投影成稀疏属性。
4. fighter 和 radar 都是 Unit，但它们可以拥有不同的 property。
5. 上层 view/agent 不再遍历 Python Unit 对象，而是查询当前本体事实。

Run:
    PYTHONPATH=. uv run python forge/core/ontology/dev_pysim_projection_example.py
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from forge.core.ontology.dev_ontology_skeleton import (
    LinkRecord,
    LinkTypeSpec,
    ObjectRecord,
    ObjectTypeSpec,
    OntologySchemaRegistry,
    OntologyStore,
    PropertySpec,
)

PYSIM_SOURCE = "pysim_mock"


def build_pysim_schema() -> OntologySchemaRegistry:
    """注册本 demo 需要的一小部分 pysim 本体定义。"""

    registry = OntologySchemaRegistry()
    registry.register_object_type(
        ObjectTypeSpec(
            name="Unit",
            interfaces=["Ownable", "Damageable", "Locatable"],
            properties={
                "name": PropertySpec("name", "string", index="keyword"),
                "side": PropertySpec("side", "string", index="keyword"),
                "unit_type": PropertySpec("unit_type", "string", index="keyword"),
                "health": PropertySpec("health", "number", index="range"),
                "position": PropertySpec("position", "struct", update_policy="current"),
                "speed": PropertySpec("speed", "number", index="range"),
                "alive": PropertySpec("alive", "bool", index="keyword"),
                "fuel": PropertySpec("fuel", "number", index="range", description="飞行单位剩余油量。"),
                "missile_count": PropertySpec(
                    "missile_count",
                    "number",
                    index="range",
                    description="飞行单位剩余空空/空地弹药数量。",
                ),
                "detection_range": PropertySpec(
                    "detection_range",
                    "number",
                    index="range",
                    description="传感器单位当前探测距离。",
                ),
                "tracked_targets": PropertySpec(
                    "tracked_targets",
                    "number",
                    index="range",
                    description="传感器单位当前跟踪目标数。",
                ),
                "emitting": PropertySpec(
                    "emitting", "bool", index="keyword", description="传感器是否开机辐射。"
                ),
            },
            description="从 pysim-like observation 投影出来的单位。",
        )
    )
    registry.register_object_type(
        ObjectTypeSpec(
            name="Side",
            properties={"name": PropertySpec("name", "string", index="keyword")},
        )
    )
    registry.register_link_type(
        LinkTypeSpec(
            name="belongs_to",
            source_types=["Unit"],
            target_types=["Side"],
            update_policy="current",
            description="单位属于某一方。",
        )
    )
    return registry


class PysimMockProjector:
    """把一帧 pysim-like observation 映射成通用 ontology records。"""

    def project(
        self, observation: dict[str, Any], *, tick: int
    ) -> tuple[list[ObjectRecord], list[LinkRecord]]:
        """投影一帧环境数据。

        Args:
            observation: 环境原始态势，demo 中只包含 ``units``。
            tick: 当前仿真 tick。

        Returns:
            可写入通用本体存储的 object/link 更新记录。
        """

        objects: list[ObjectRecord] = []
        links: list[LinkRecord] = []

        for unit_id, unit_payload in observation.get("units", {}).items():
            unit_object_id = self._object_id("Unit", unit_id)
            side_name = str(unit_payload["side"])
            side_object_id = self._object_id("Side", side_name)

            # 注意：这里没有构造 Unit Python 实体；只把环境字段展开为本体属性。
            # 不同 unit_type 可以带不同字段，缺失字段不会写入 property_values。
            unit_properties = {
                "name": unit_payload.get("name", unit_id),
                "side": side_name,
                "unit_type": unit_payload.get("unit_type", "unknown"),
                "health": unit_payload.get("health", 0),
                "position": unit_payload.get("position", {}),
                "speed": unit_payload.get("speed", 0),
                "alive": unit_payload.get("alive", True),
            }
            for optional_name in (
                "fuel",
                "missile_count",
                "detection_range",
                "tracked_targets",
                "emitting",
            ):
                if optional_name in unit_payload:
                    unit_properties[optional_name] = unit_payload[optional_name]

            objects.append(
                ObjectRecord(
                    object_id=unit_object_id,
                    object_type="Unit",
                    source=PYSIM_SOURCE,
                    source_type="Unit",
                    source_id=unit_id,
                    properties=unit_properties,
                )
            )
            # Side 也是 object，所以 UI 和查询层可以直接围绕阵营对象建视图。
            objects.append(
                ObjectRecord(
                    object_id=side_object_id,
                    object_type="Side",
                    source=PYSIM_SOURCE,
                    source_type="Side",
                    source_id=side_name,
                    properties={"name": side_name},
                )
            )
            # belongs_to 是当前态 link；如果未来阵营归属会变化，也可以持续 upsert。
            links.append(
                LinkRecord(
                    link_type="belongs_to",
                    source_id=unit_object_id,
                    target_id=side_object_id,
                    source=PYSIM_SOURCE,
                )
            )

        return objects, links

    def _object_id(self, object_type: str, source_id: str) -> str:
        """用 source namespace 保证本体 ID 稳定且不和其他环境冲突。"""

        return f"{object_type.lower()}:{PYSIM_SOURCE}:{source_id}"


def demo() -> None:
    """投影两帧小态势，并打印当前本体状态。"""

    registry = build_pysim_schema()
    projector = PysimMockProjector()
    print(
        "registered_schema",
        {
            "object_types": sorted(registry.object_types),
            "link_types": sorted(registry.link_types),
        },
    )
    observations = [
        {
            "units": {
                "blue_fighter_1": {
                    "name": "blue fighter 1",
                    "side": "blue",
                    "unit_type": "fighter",
                    "health": 100,
                    "position": {"x": 0, "y": 10, "z": 5},
                    "speed": 12,
                    "alive": True,
                    "fuel": 80,
                    "missile_count": 4,
                },
                "blue_radar_1": {
                    "name": "blue radar 1",
                    "side": "blue",
                    "unit_type": "radar",
                    "health": 96,
                    "position": {"x": 2, "y": 12, "z": 5},
                    "speed": 0,
                    "alive": True,
                    "detection_range": 120,
                    "tracked_targets": 1,
                    "emitting": True,
                },
                "red_radar_1": {
                    "name": "red radar 1",
                    "side": "red",
                    "unit_type": "radar",
                    "health": 100,
                    "position": {"x": 50, "y": 50, "z": 0},
                    "speed": 0,
                    "alive": True,
                    "detection_range": 160,
                    "tracked_targets": 2,
                    "emitting": True,
                },
            }
        },
        {
            "units": {
                "blue_fighter_1": {
                    "name": "blue fighter 1",
                    "side": "blue",
                    "unit_type": "fighter",
                    "health": 96,
                    "position": {"x": 10, "y": 20, "z": 5},
                    "speed": 14,
                    "alive": True,
                    "fuel": 64,
                    "missile_count": 3,
                },
                "blue_radar_1": {
                    "name": "blue radar 1",
                    "side": "blue",
                    "unit_type": "radar",
                    "health": 92,
                    "position": {"x": 12, "y": 22, "z": 5},
                    "speed": 0,
                    "alive": True,
                    "detection_range": 135,
                    "tracked_targets": 3,
                    "emitting": True,
                },
                "red_radar_1": {
                    "name": "red radar 1",
                    "side": "red",
                    "unit_type": "radar",
                    "health": 76,
                    "position": {"x": 50, "y": 50, "z": 0},
                    "speed": 0,
                    "alive": True,
                    "detection_range": 150,
                    "tracked_targets": 1,
                    "emitting": False,
                },
            }
        },
    ]

    with TemporaryDirectory(prefix="forge_pysim_projection_") as tmp_dir:
        store = OntologyStore(Path(tmp_dir) / "ontology.sqlite")
        for tick, observation in enumerate(observations, start=1):
            objects, links = projector.project(observation, tick=tick)
            store.apply_records(objects, links, tick=tick)
            healthy_blue_units = store.query_objects(
                "Unit",
                filters={"side": "blue"},
                number_gt={"health": 90},
            )
            armed_blue_fighters = store.query_objects(
                "Unit",
                filters={"side": "blue", "unit_type": "fighter"},
                number_gt={"missile_count": 0},
            )
            active_blue_radars = store.query_objects(
                "Unit",
                filters={"side": "blue", "unit_type": "radar", "emitting": True},
                number_gt={"detection_range": 100},
            )
            print(
                {
                    "tick": tick,
                    "projected_objects": len(objects),
                    "projected_links": len(links),
                    "healthy_blue_units": [item["object_id"] for item in healthy_blue_units],
                    "armed_blue_fighters": [item["object_id"] for item in armed_blue_fighters],
                    "active_blue_radars": [item["object_id"] for item in active_blue_radars],
                }
            )

        print("selected_unit_properties", _selected_unit_properties(store))
        print("objects", store.dump_table("objects"))
        print("identities", store.dump_table("object_identities"))
        print("links", store.dump_table("links"))
        _print_development_notes()
        store.close()


def _selected_unit_properties(store: OntologyStore) -> list[dict[str, Any]]:
    """只打印最能说明数据流的 Unit 属性，避免 dev 输出太吵。"""

    rows = store.dump_table("property_values")
    return [
        {
            "object_id": row["object_id"],
            "property_name": row["property_name"],
            "value_text": row["value_text"],
            "value_number": row["value_number"],
            "value_bool": row["value_bool"],
            "updated_tick": row["updated_tick"],
        }
        for row in rows
        if row["object_type"] == "Unit"
        and row["property_name"]
        in {
            "side",
            "unit_type",
            "health",
            "speed",
            "fuel",
            "missile_count",
            "detection_range",
            "tracked_targets",
            "emitting",
        }
    ]


def _print_development_notes() -> None:
    """在脚本最后用具体例子解释这次投影表达了什么。"""

    print(
        "说明",
        [
            "blue_fighter_1 来自 pysim 环境 ID，稳定映射为 unit:pysim_mock:blue_fighter_1。",
            "fighter 和 radar 都是 Unit，共享 side/health/position，但各自拥有不同的稀疏属性。",
            "blue_fighter_1 有 fuel/missile_count；blue_radar_1 有 detection_range/tracked_targets/emitting。",
            "查询 armed_blue_fighters 时只要求 missile_count>0，因此 radar 不会被误选。",
            "查询 active_blue_radars 时只要求 radar 的 detection_range>100 且 emitting=True。",
            "belongs_to link 把 Unit 关联到 Side，展示层可以直接从本体拼出蓝方/红方视图。",
        ],
    )


if __name__ == "__main__":
    demo()
