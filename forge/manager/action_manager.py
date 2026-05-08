from __future__ import annotations

from typing import Union

from forge.lib.action import ActionParams
from forge.manager.manager import Manager


class ActionManager(Manager):
    """Maintains pending and active action parameters."""

    def __init__(self, agent: object, config: dict, manager_hub):
        super().__init__(agent, config, manager_hub)
        self.actions: list[ActionParams] = []

    def reset(self) -> None:
        self.actions.clear()

    async def update(self, **kwargs) -> None:
        actions = kwargs.get("actions")
        if actions:
            self.add_action(actions)

    def step(self) -> list[ActionParams]:
        return list(self.actions)

    def add_action(self, action: Union[list[ActionParams], ActionParams]) -> None:
        if isinstance(action, list):
            self.actions.extend(action)
            return
        self.actions.append(action)
