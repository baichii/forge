from __future__ import annotations

import importlib
from typing import Any

from pydantic import BaseModel, Field, create_model

from forge.lib.agent import TickAgent
from forge.utils.specs import TickAgentSpec


class TickAgentRuntimeContext(BaseModel):
    side: str = "blue"
    agent_name: str = "battle_planner"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TickAgentFactory:
    @staticmethod
    def validate_params(declaration: TickAgentSpec, params: dict[str, Any]) -> BaseModel:
        fields: dict[str, tuple[type[Any], Any]] = {}
        for param in declaration.params.values():
            py_type = _to_python_type(param.type)
            default = ... if param.required and param.default_value is None else param.default_value
            fields[param.name] = (py_type, default)

        params_model = create_model(f"{declaration.name.title().replace('_', '')}Params", **fields)
        return params_model.model_validate(params)

    @staticmethod
    def create(
        declaration: TickAgentSpec,
        params: dict[str, Any],
        runtime_context: TickAgentRuntimeContext | None = None,
    ) -> TickAgent:
        if declaration.entrypoint is None:
            msg = f"Tick agent '{declaration.name}' has no entrypoint."
            raise ValueError(msg)

        agent_cls = _load_entrypoint(declaration.entrypoint)
        validated_params = TickAgentFactory.validate_params(declaration, params)
        return agent_cls(
            params=validated_params,
            runtime_context=runtime_context or TickAgentRuntimeContext(),
        )


def _load_entrypoint(entrypoint: str) -> type[TickAgent]:
    module_name, attr_name = entrypoint.split(":", 1)
    module = importlib.import_module(module_name)
    agent_cls = getattr(module, attr_name)
    return agent_cls


def _to_python_type(type_name: str) -> type[Any]:
    type_map: dict[str, type[Any]] = {
        "str": str,
        "string": str,
        "int": int,
        "float": float,
        "bool": bool,
        "dict": dict,
        "list": list,
        "list[str]": list,
        "list[int]": list,
        "list[float]": list,
    }
    return type_map.get(type_name, Any)
