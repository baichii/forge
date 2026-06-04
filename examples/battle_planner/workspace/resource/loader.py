from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from forge.core.specs import TickAgentSpec
from forge.registration import register_tick_agent, registry

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
RESOURCE_ROOT = BATTLE_PLANNER_ROOT / "workspace" / "resource"
TICK_AGENT_ROOT = RESOURCE_ROOT / "tick_agents"
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
        TickAgentSpec.model_validate(
            {
                **descriptor.payload,
                "entrypoint": descriptor.resolved_entrypoint,
            }
        )
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
    descriptors = [
        _load_tick_agent_descriptor(config_path)
        for config_path in sorted(TICK_AGENT_ROOT.glob("*/config.yaml"))
    ]
    return descriptors


def _load_tick_agent_descriptor(config_path: Path) -> ResourceDescriptor:
    payload = _read_yaml(config_path)
    relative_entrypoint = str(payload.get("entrypoint") or DEFAULT_TICK_AGENT_ENTRYPOINT)
    resolved_entrypoint = _resolve_entrypoint(
        root=config_path.parent,
        relative_entrypoint=relative_entrypoint,
        resource_type="tick_agents",
    )
    return ResourceDescriptor(
        kind="tick_agent",
        name=str(payload["name"]),
        version=str(payload.get("version") or ""),
        root=config_path.parent,
        relative_entrypoint=relative_entrypoint,
        resolved_entrypoint=resolved_entrypoint,
        payload=payload,
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"resource config `{path}` must contain a mapping")
    return payload


def _resolve_entrypoint(*, root: Path, relative_entrypoint: str, resource_type: str) -> str:
    module_name, separator, attribute_name = relative_entrypoint.partition(":")
    if not module_name or not attribute_name or separator != ":":
        raise ValueError(f"invalid resource entrypoint `{relative_entrypoint}` in `{root}`")
    if module_name.startswith("."):
        raise ValueError(f"relative entrypoint `{relative_entrypoint}` must not start with `.`")

    resource_name = root.name
    normalized_module_name = module_name.replace("/", ".")
    return f"{RESOURCE_PACKAGE}.{resource_type}.{resource_name}.{normalized_module_name}:{attribute_name}"
