"""基于本体的仿真态势存储骨架示例。

这个文件刻意保持小而通用，用来讨论未来可能沉淀到 ``forge.core`` 的部分：

- 开放 schema registry：不同环境可以注册自己的 object/property/link 类型。
- source identity mapping：环境里的单位 ID 先映射成稳定的 ontology object_id。
- SQLite 当前态表：UI、查询、runtime 都可以直接读取本体事实。

这个骨架不认识任何 pysim 专有字段；具体环境字段应该放到 adapter 示例里。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class PropertySpec:
    """稀疏本体属性的 schema 元信息。"""

    name: str = field(metadata={"description": "属性名称，例如 health、side、position。"})
    value_type: str = field(metadata={"description": "属性值类型，例如 string、number、bool、struct。"})
    index: str = field(
        default="none", metadata={"description": "建议索引类型，例如 none、keyword、range。"}
    )
    update_policy: str = field(
        default="current", metadata={"description": "属性更新策略，例如 current、event、history。"}
    )
    description: str = field(default="", metadata={"description": "面向业务和工具展示的属性说明。"})


@dataclass(frozen=True)
class ObjectTypeSpec:
    """环境注册的某类 object type 元信息。"""

    name: str = field(metadata={"description": "对象类型名称，例如 Unit、Side、MapArea。"})
    properties: dict[str, PropertySpec] = field(
        default_factory=dict,
        metadata={"description": "该对象类型可使用的属性定义，允许不同对象只写入其中一部分。"},
    )
    interfaces: list[str] = field(
        default_factory=list,
        metadata={"description": "对象实现的能力接口，例如 Ownable、Damageable、Locatable。"},
    )
    description: str = field(default="", metadata={"description": "面向业务和工具展示的对象类型说明。"})


@dataclass(frozen=True)
class LinkTypeSpec:
    """某类 link type 的元信息。"""

    name: str = field(metadata={"description": "关系类型名称，例如 belongs_to、attacking、located_in。"})
    source_types: list[str] = field(
        default_factory=list,
        metadata={"description": "允许作为关系起点的对象类型列表；为空表示 dev 阶段暂不限制。"},
    )
    target_types: list[str] = field(
        default_factory=list,
        metadata={"description": "允许作为关系终点的对象类型列表；为空表示 dev 阶段暂不限制。"},
    )
    update_policy: str = field(
        default="current", metadata={"description": "关系更新策略，例如 current、event、history。"}
    )
    description: str = field(default="", metadata={"description": "面向业务和工具展示的关系类型说明。"})


@dataclass(frozen=True)
class ObjectRecord:
    """环境 projector 产出的一条 object 更新。"""

    object_id: str = field(
        metadata={"description": "稳定的本体对象 ID，例如 unit:pysim_mock:blue_fighter_1。"}
    )
    object_type: str = field(metadata={"description": "对象类型名称，必须能对应到 ObjectTypeSpec.name。"})
    properties: dict[str, Any] = field(
        metadata={"description": "本帧写入的稀疏属性值；未出现的属性不会被创建。"}
    )
    source: str = field(
        metadata={"description": "数据来源命名空间，例如 pysim_mock、pysim、battle_planner。"}
    )
    source_type: str = field(metadata={"description": "环境原始对象类型，例如 Unit、Side、SensorTrack。"})
    source_id: str = field(
        metadata={"description": "环境原始对象 ID，用于维护 source_id 到 object_id 的映射。"}
    )


@dataclass(frozen=True)
class LinkRecord:
    """环境 projector 产出的一条 link 更新。"""

    link_type: str = field(metadata={"description": "关系类型名称，必须能对应到 LinkTypeSpec.name。"})
    source_id: str = field(metadata={"description": "关系起点对象的稳定本体 object_id。"})
    target_id: str = field(metadata={"description": "关系终点对象的稳定本体 object_id。"})
    source: str = field(metadata={"description": "产生该关系的数据来源命名空间。"})


class ObservationProjector(Protocol):
    """环境侧 adapter：把 observation payload 投影成本体记录。"""

    def project(
        self, observation: dict[str, Any], *, tick: int
    ) -> tuple[list[ObjectRecord], list[LinkRecord]]:
        """把一帧 observation 投影成 object/link 记录。"""


class OntologySchemaRegistry:
    """开放 schema registry，供环境 adapter 和 view 共享。"""

    def __init__(self):
        self.object_types: dict[str, ObjectTypeSpec] = {}
        self.link_types: dict[str, LinkTypeSpec] = {}

    def register_object_type(self, spec: ObjectTypeSpec) -> None:
        self.object_types[spec.name] = spec

    def register_link_type(self, spec: LinkTypeSpec) -> None:
        self.link_types[spec.name] = spec


class OntologyStore:
    """开发实验用的 SQLite-backed ontology 当前态存储。"""

    def __init__(self, db_path: str | Path = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;

            CREATE TABLE IF NOT EXISTS objects (
                object_id TEXT PRIMARY KEY,
                object_type TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                updated_tick INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS object_identities (
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                object_id TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                updated_tick INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (source, source_type, source_id)
            );

            CREATE TABLE IF NOT EXISTS property_values (
                object_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                property_name TEXT NOT NULL,
                value_text TEXT,
                value_number REAL,
                value_bool INTEGER,
                value_json TEXT,
                updated_tick INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (object_id, property_name)
            );

            CREATE TABLE IF NOT EXISTS links (
                link_id TEXT PRIMARY KEY,
                link_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                updated_tick INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                object_id TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_objects_type
                ON objects(object_type, active);
            CREATE INDEX IF NOT EXISTS idx_identity_object
                ON object_identities(object_id, active);
            CREATE INDEX IF NOT EXISTS idx_property_text
                ON property_values(object_type, property_name, value_text);
            CREATE INDEX IF NOT EXISTS idx_property_number
                ON property_values(object_type, property_name, value_number);
            CREATE INDEX IF NOT EXISTS idx_links_source
                ON links(link_type, source_id, active);
            CREATE INDEX IF NOT EXISTS idx_links_target
                ON links(link_type, target_id, active);
            """
        )
        self.conn.commit()

    def apply_records(self, objects: list[ObjectRecord], links: list[LinkRecord], *, tick: int) -> None:
        """在单个事务里应用一帧投影结果。"""

        with self.conn:
            for record in objects:
                self.upsert_object(record, tick=tick)
            for record in links:
                self.upsert_link(record, tick=tick)

    def upsert_object(self, record: ObjectRecord, *, tick: int) -> None:
        """插入或更新 object，并维护 source_id 到 object_id 的映射。"""

        self.conn.execute(
            """
            INSERT INTO objects(object_id, object_type, active, updated_tick)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(object_id) DO UPDATE SET
                object_type=excluded.object_type,
                active=1,
                updated_tick=excluded.updated_tick
            """,
            (record.object_id, record.object_type, tick),
        )
        self.conn.execute(
            """
            INSERT INTO object_identities(source, source_type, source_id, object_id, active, updated_tick)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(source, source_type, source_id) DO UPDATE SET
                object_id=excluded.object_id,
                active=1,
                updated_tick=excluded.updated_tick
            """,
            (record.source, record.source_type, record.source_id, record.object_id, tick),
        )
        self.conn.executemany(
            """
            INSERT INTO property_values(
                object_id, object_type, property_name,
                value_text, value_number, value_bool, value_json, updated_tick
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(object_id, property_name) DO UPDATE SET
                object_type=excluded.object_type,
                value_text=excluded.value_text,
                value_number=excluded.value_number,
                value_bool=excluded.value_bool,
                value_json=excluded.value_json,
                updated_tick=excluded.updated_tick
            """,
            [
                (
                    record.object_id,
                    record.object_type,
                    name,
                    value if isinstance(value, str) else None,
                    float(value) if _is_number(value) else None,
                    int(value) if isinstance(value, bool) else None,
                    json.dumps(value, ensure_ascii=False) if _is_json_value(value) else None,
                    tick,
                )
                for name, value in record.properties.items()
            ],
        )
        self.record_event(
            "object_upserted",
            tick=tick,
            object_id=record.object_id,
            payload={
                "object_type": record.object_type,
                "source": record.source,
                "source_type": record.source_type,
                "source_id": record.source_id,
                "properties": sorted(record.properties),
            },
        )

    def upsert_link(self, record: LinkRecord, *, tick: int) -> None:
        """插入或刷新一条当前态 link。"""

        link_id = f"{record.link_type}:{record.source_id}->{record.target_id}"
        self.conn.execute(
            """
            INSERT INTO links(link_id, link_type, source_id, target_id, source, active, updated_tick)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(link_id) DO UPDATE SET
                source=excluded.source,
                active=1,
                updated_tick=excluded.updated_tick
            """,
            (link_id, record.link_type, record.source_id, record.target_id, record.source, tick),
        )
        self.record_event(
            "link_upserted",
            tick=tick,
            object_id=record.source_id,
            payload={
                "link_type": record.link_type,
                "source_id": record.source_id,
                "target_id": record.target_id,
                "source": record.source,
            },
        )

    def record_event(
        self,
        event_type: str,
        *,
        tick: int,
        object_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO events(tick, event_type, object_id, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (tick, event_type, object_id, json.dumps(payload or {}, ensure_ascii=False)),
        )

    def query_objects(
        self,
        object_type: str,
        *,
        filters: dict[str, Any] | None = None,
        number_gt: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        """通过稀疏属性表 join 查询当前态 object。"""

        filters = filters or {}
        number_gt = number_gt or {}
        joins: list[str] = []
        join_params: list[Any] = []
        where = ["o.object_type = ?", "o.active = 1"]
        where_params: list[Any] = [object_type]

        for index, (name, value) in enumerate(filters.items()):
            alias = f"p_filter_{index}"
            if isinstance(value, bool):
                joins.append(
                    f"""
                    JOIN property_values {alias}
                      ON {alias}.object_id = o.object_id
                     AND {alias}.property_name = ?
                     AND {alias}.value_bool = ?
                    """
                )
                join_params.extend([name, int(value)])
            else:
                joins.append(
                    f"""
                    JOIN property_values {alias}
                      ON {alias}.object_id = o.object_id
                     AND {alias}.property_name = ?
                     AND {alias}.value_text = ?
                    """
                )
                join_params.extend([name, str(value)])

        for index, (name, value) in enumerate(number_gt.items()):
            alias = f"p_num_{index}"
            joins.append(
                f"""
                JOIN property_values {alias}
                  ON {alias}.object_id = o.object_id
                 AND {alias}.property_name = ?
                 AND {alias}.value_number > ?
                """
            )
            join_params.extend([name, value])

        rows = self.conn.execute(
            f"""
            SELECT o.object_id, o.object_type, o.updated_tick
            FROM objects o
            {" ".join(joins)}
            WHERE {" AND ".join(where)}
            ORDER BY o.object_id
            """,
            [*join_params, *where_params],
        ).fetchall()
        return [dict(row) for row in rows]

    def dump_table(self, table: str) -> list[dict[str, Any]]:
        """导出 dev 表内容，便于 demo 打印和测试断言。"""

        if table not in {"objects", "object_identities", "property_values", "links", "events"}:
            raise ValueError(f"Unsupported table: {table}")
        return [dict(row) for row in self.conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_json_value(value: Any) -> bool:
    return isinstance(value, dict | list)
