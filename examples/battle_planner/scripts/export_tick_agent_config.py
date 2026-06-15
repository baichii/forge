"""导出 tick-agent 配置文件。

Notes:
    用于根据资源声明生成本地 config.yaml。
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TICK_AGENT_ROOT = REPO_ROOT / "examples" / "battle_planner" / "workspace" / "resource" / "tick_agents"
TICK_AGENT_PACKAGE = "battle_planner.workspace.resource.tick_agents"
START_META_ID = 10001

TYPE_LABELS = {
    "int": "整数",
    "float": "浮点数",
    "bool": "布尔值",
    "string": "字符串",
    "list": "列表",
    "datetime": "时间",
    "table": "表格",
    "enum_s": "单选",
    "enum_m": "多选",
    "area": "区域",
    "named_area": "命名区域",
    "route": "路径",
}


def _str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, _str_representer)


def main() -> None:
    agent_dirs = _tick_agent_dirs()
    if not agent_dirs:
        raise ValueError(f"No tick-agent packages found in {TICK_AGENT_ROOT}")

    for offset, agent_dir in enumerate(agent_dirs):
        meta_id = START_META_ID + offset
        declaration = _load_declaration(agent_dir.name)
        payload = _config_payload(declaration, meta_id=meta_id)
        output = agent_dir / "config.yaml"
        output.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"exported {meta_id} {declaration.name} config to {output}")

    print(f"exported {len(agent_dirs)} tick-agent configs")


def _tick_agent_dirs() -> list[Path]:
    return sorted(
        path for path in TICK_AGENT_ROOT.iterdir() if path.is_dir() and (path / "agent.py").exists()
    )


def _load_declaration(package_name: str) -> Any:
    module = importlib.import_module(f"{TICK_AGENT_PACKAGE}.{package_name}.agent")
    return module.declaration


def _config_payload(declaration: Any, *, meta_id: int) -> dict[str, Any]:
    return {
        "META": {
            "id": meta_id,
            "name": declaration.name,
            "description": declaration.description,
        },
        "PARAMS": [_param_payload(param_key, param) for param_key, param in declaration.params.items()],
        "STATUS": list(declaration.status),
        "VERSION": declaration.version,
    }


def _param_payload(param_key: str, param: Any) -> dict[str, Any]:
    return {
        "name": param_key,
        "type": TYPE_LABELS.get(param.type, param.type),
        "default_value": param.default_value,
        "chineseName": param.name,
        "description": param.description,
        "required": param.required,
    }


if __name__ == "__main__":
    main()
