from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from forge.utils import construct


class ManagerHubConfig(BaseModel):
    managers: dict[str, dict[str, Any]] = Field(default_factory=dict, description="manager registry")


class ManagerHub:
    """Container and mediator for situation managers."""

    def __init__(self, agent: object, config: ManagerHubConfig):
        self.agent = agent
        self.config = config
        self.managers = {}

        for manager_name, manager_class_dict in self.config.managers.items():
            self.managers[manager_name] = construct(
                manager_class_dict,
                agent=agent,
                manager_hub=self,
            )

    def reset(self) -> None:
        for manager in self.managers.values():
            manager.reset()

    def initialise(self) -> None:
        for manager in self.managers.values():
            manager.initialise()

    async def update(self, **kwargs) -> None:
        for manager in self.managers.values():
            await manager.update(**kwargs)

    def get(self, name: str) -> object:
        return self.managers[name]
