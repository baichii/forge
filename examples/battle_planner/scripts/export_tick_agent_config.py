from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TICK_AGENT_ROOT = REPO_ROOT / "examples" / "battle_planner" / "workspace" / "resource" / "tick_agents"
TICK_AGENT_PACKAGE = "battle_planner.workspace.resource.tick_agents"

DEFAULT_DECLARATION_ATTRIBUTE = "declaration"
DEFAULT_START_META_ID = 10001


def _str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, _str_representer)


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


def main() -> None:
    args = _parse_args()
    if args.declaration:
        output = Path(args.output) if args.output else None
        meta_id = args.meta_id if args.meta_id is not None else args.start_meta_id
        _export_declaration(args.declaration, meta_id=meta_id, output=output)
        return

    _export_tick_agent_root(
        tick_agent_root=Path(args.tick_agent_root),
        start_meta_id=args.start_meta_id,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a tick-agent declaration to config.yaml.")
    parser.add_argument(
        "--declaration",
        default="",
        help="Optional declaration import path in module:attribute form. If omitted, export all tick-agents.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output config.yaml path. Only used with --declaration.",
    )
    parser.add_argument(
        "--meta-id",
        type=int,
        default=None,
        help="META.id value for single declaration export. Defaults to --start-meta-id.",
    )
    parser.add_argument(
        "--tick-agent-root",
        default=str(TICK_AGENT_ROOT),
        help="Root directory that contains tick-agent package directories.",
    )
    parser.add_argument(
        "--start-meta-id",
        type=int,
        default=DEFAULT_START_META_ID,
        help="First META.id value for batch export. Each tick-agent increments by 1.",
    )
    return parser.parse_args()


def _export_tick_agent_root(*, tick_agent_root: Path, start_meta_id: int) -> None:
    exported = []
    for offset, agent_dir in enumerate(_iter_tick_agent_dirs(tick_agent_root)):
        import_path = _declaration_import_path(agent_dir)
        output = agent_dir / "config.yaml"
        payload = _export_declaration(import_path, meta_id=start_meta_id + offset, output=output)
        exported.append((payload["META"]["id"], payload["META"]["name"], output))

    if not exported:
        raise ValueError(f"No tick-agent packages found in {tick_agent_root}")

    print(f"exported {len(exported)} tick-agent configs")


def _iter_tick_agent_dirs(tick_agent_root: Path) -> list[Path]:
    return sorted(
        path for path in tick_agent_root.iterdir() if path.is_dir() and (path / "agent.py").exists()
    )


def _declaration_import_path(agent_dir: Path) -> str:
    return f"{TICK_AGENT_PACKAGE}.{agent_dir.name}.agent:{DEFAULT_DECLARATION_ATTRIBUTE}"


def _export_declaration(import_path: str, *, meta_id: int, output: Path | None) -> dict[str, Any]:
    declaration = _load_declaration(import_path)
    payload = _build_config_payload(declaration, meta_id=meta_id)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"exported {payload['META']['id']} {payload['META']['name']} config to {output}")
    return payload


def _load_declaration(import_path: str) -> Any:
    module_name, _, attribute_name = import_path.partition(":")
    if not module_name or not attribute_name:
        raise ValueError(f"Invalid declaration import path: {import_path}")
    module = importlib.import_module(module_name)
    return getattr(module, attribute_name)


def _build_config_payload(declaration: Any, *, meta_id: int) -> dict[str, Any]:
    return {
        "META": {
            "id": meta_id,
            "name": declaration.name,
            "description": declaration.description,
        },
        "PARAMS": [_build_param_payload(param) for param in declaration.params.values()],
        "STATUS": list(declaration.status),
        "VERSION": declaration.version,
    }


def _build_param_payload(param: Any) -> dict[str, Any]:
    other = dict(param.other or {})
    return {
        "name": param.name,
        "type": _type_label(param.type),
        "default_value": param.default_value,
        "chineseName": _chinese_name(param.name, other),
        "description": param.description,
        "required": param.required,
    }


def _type_label(value: str) -> str:
    return TYPE_LABELS.get(value, value)


def _chinese_name(name: str, other: dict[str, Any]) -> str:
    value = other.get("chineseName") or other.get("chinese_name") or other.get("zh_name")
    return str(value) if value else name


if __name__ == "__main__":
    main()
