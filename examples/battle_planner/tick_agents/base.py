from __future__ import annotations

import importlib
from typing import Any

from forge.lib.agent import TickAgent
from forge.utils.specs import TickAgentSpec


class TickAgentFactory:
    @staticmethod
    def create(
        declaration: TickAgentSpec,
        params: dict[str, Any],
    ) -> TickAgent:
        if declaration.entrypoint is None:
            msg = f"Tick agent '{declaration.name}' has no entrypoint."
            raise ValueError(msg)

        agent_cls = _load_entrypoint(declaration.entrypoint)
        return agent_cls(params=params)


def _load_entrypoint(entrypoint: str) -> type[TickAgent]:
    module_name, attr_name = entrypoint.split(":", 1)
    module = importlib.import_module(module_name)
    agent_cls = getattr(module, attr_name)
    return agent_cls
