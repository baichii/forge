from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from forge.core.specs import TickAgentSpec
from forge.registration import register_tick_agent, registry

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
TICK_AGENT_ROOT = BATTLE_PLANNER_ROOT / "workspace" / "resource" / "tick_agents"
RESOURCE_PACKAGE = "battle_planner.workspace.resource"
DEFAULT_TICK_AGENT_ENTRYPOINT = "agent:Agent"


@dataclass(frozen=True)
class ResourceDescriptor:
    kind: str
    name: str
    version: str
    root: Path
    relative_entrypoint: str
    resolved_entrypoint: str
    payload: dict[str, Any]


def load_tick_agent_specs() -> list[TickAgentSpec]:
    return [
        TickAgentSpec.model_validate({**descriptor.payload, "entrypoint": descriptor.resolved_entrypoint})
        for descriptor in iter_tick_agent_resources()
    ]


def register_tick_agent_resources() -> None:
    for descriptor in iter_tick_agent_resources():
        module_id = f"tick_agent/{descriptor.name}"
        if module_id in registry:
            continue
        register_tick_agent(
            descriptor.name,
            descriptor.resolved_entrypoint,
            data={
                "resource_root": str(descriptor.root),
                "relative_entrypoint": descriptor.relative_entrypoint,
                "version": descriptor.version,
            },
        )


def iter_tick_agent_resources() -> list[ResourceDescriptor]:
    return [
        _load_tick_agent(agent_dir)
        for agent_dir in sorted(TICK_AGENT_ROOT.iterdir())
        if agent_dir.is_dir() and (agent_dir / "config.yaml").exists()
    ]


def _load_tick_agent(agent_dir: Path) -> ResourceDescriptor:
    config = _read_yaml(agent_dir / "config.yaml")
    meta = config["META"]
    relative_entrypoint = str(config.get("ENTRYPOINT") or DEFAULT_TICK_AGENT_ENTRYPOINT)
    resolved_entrypoint = _resolve_entrypoint(agent_dir=agent_dir, relative_entrypoint=relative_entrypoint)
    payload = {
        "name": _internal_agent_name(agent_dir),
        "description": str(meta.get("description") or ""),
        "params": {
            str(param["name"]): {
                "name": str(param["name"]),
                "type": str(param.get("type") or ""),
                "required": bool(param.get("required", True)),
                "description": str(param.get("description") or ""),
                "default_value": param.get("default_value"),
                "examples": list(param.get("examples") or []),
                "other": {"chineseName": param["chineseName"]} if param.get("chineseName") else {},
            }
            for param in config.get("PARAMS", [])
        },
        "entrypoint": relative_entrypoint,
        "status": [str(item) for item in config.get("STATUS", [])],
        "version": str(config.get("VERSION") or ""),
    }
    return ResourceDescriptor(
        kind="tick_agent",
        name=payload["name"],
        version=payload["version"],
        root=agent_dir,
        relative_entrypoint=relative_entrypoint,
        resolved_entrypoint=resolved_entrypoint,
        payload=payload,
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"resource config `{path}` must contain a mapping")
    return payload


def _internal_agent_name(agent_dir: Path) -> str:
    return f"{agent_dir.name}_agent"


def _resolve_entrypoint(*, agent_dir: Path, relative_entrypoint: str) -> str:
    module_name, separator, attribute_name = relative_entrypoint.partition(":")
    if not module_name or not attribute_name or separator != ":":
        raise ValueError(f"invalid resource entrypoint `{relative_entrypoint}` in `{agent_dir}`")
    normalized_module_name = module_name.replace("/", ".")
    return f"{RESOURCE_PACKAGE}.tick_agents.{agent_dir.name}.{normalized_module_name}:{attribute_name}"
