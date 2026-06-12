from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from forge.core.specs import CallbackSpec, TickAgentSpec
from forge.registration import register_callback, register_tick_agent, registry

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
TICK_AGENT_ROOT = BATTLE_PLANNER_ROOT / "workspace" / "resource" / "tick_agents"
CALLBACK_ROOT = BATTLE_PLANNER_ROOT / "workspace" / "resource" / "callbacks"
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


def load_callback_specs() -> list[CallbackSpec]:
    return [
        CallbackSpec.model_validate(
            {
                **_load_declaration(descriptor).model_dump(),
                "entrypoint": descriptor.resolved_entrypoint,
            }
        )
        for descriptor in iter_callback_resources()
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


def register_callback_resources() -> None:
    for descriptor in iter_callback_resources():
        module_id = f"callback/{descriptor.name}"
        if module_id in registry:
            continue
        register_callback(
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


def iter_callback_resources() -> list[ResourceDescriptor]:
    return [
        descriptor
        for callback_file in sorted(CALLBACK_ROOT.glob("*.py"))
        if (descriptor := _load_callback(callback_file)) is not None
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


def _load_callback(callback_file: Path) -> ResourceDescriptor | None:
    if callback_file.name == "__init__.py" or callback_file.stem.startswith("_"):
        return None

    entrypoint = _read_module_entrypoint(callback_file)
    if not entrypoint:
        return None

    resolved_entrypoint = _resolve_callback_entrypoint(
        callback_file=callback_file,
        relative_entrypoint=entrypoint,
    )
    return ResourceDescriptor(
        kind="callback",
        name=callback_file.stem,
        version="",
        root=callback_file,
        relative_entrypoint=entrypoint,
        resolved_entrypoint=resolved_entrypoint,
        payload={"name": callback_file.stem, "entrypoint": entrypoint},
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"resource config `{path}` must contain a mapping")
    return payload


def _read_module_entrypoint(path: Path) -> str | None:
    module_ast = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module_ast.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "ENTRYPOINT" for target in node.targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
        raise ValueError(f"ENTRYPOINT in `{path}` must be a string literal")
    return None


def _load_declaration(descriptor: ResourceDescriptor) -> CallbackSpec:
    module_name, attribute_name = descriptor.resolved_entrypoint.rsplit(":", 1)
    module = importlib.import_module(module_name)
    callback_class = getattr(module, attribute_name)
    declaration = callback_class.declaration
    return CallbackSpec.model_validate(declaration)


def _internal_agent_name(agent_dir: Path) -> str:
    return f"{agent_dir.name}_agent"


def _resolve_entrypoint(*, agent_dir: Path, relative_entrypoint: str) -> str:
    module_name, separator, attribute_name = relative_entrypoint.partition(":")
    if not module_name or not attribute_name or separator != ":":
        raise ValueError(f"invalid resource entrypoint `{relative_entrypoint}` in `{agent_dir}`")
    normalized_module_name = module_name.replace("/", ".")
    return f"{RESOURCE_PACKAGE}.tick_agents.{agent_dir.name}.{normalized_module_name}:{attribute_name}"


def _resolve_callback_entrypoint(*, callback_file: Path, relative_entrypoint: str) -> str:
    if ":" in relative_entrypoint:
        module_name, separator, attribute_name = relative_entrypoint.partition(":")
        if not module_name or not attribute_name or separator != ":":
            raise ValueError(f"invalid callback entrypoint `{relative_entrypoint}` in `{callback_file}`")
        normalized_module_name = module_name.replace("/", ".")
        return f"{RESOURCE_PACKAGE}.callbacks.{normalized_module_name}:{attribute_name}"
    return f"{RESOURCE_PACKAGE}.callbacks.{callback_file.stem}:{relative_entrypoint}"
