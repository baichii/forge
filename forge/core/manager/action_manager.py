from __future__ import annotations

from typing import TYPE_CHECKING, Union

from forge.core.lib.action import Action, ActionParams, ActionStatus
from forge.core.manager.manager import Manager
from forge.registration import make_action
from forge.utils import construct, make_id_generator

if TYPE_CHECKING:
    from forge.core.manager.hub import ManagerHub


class ActionManager(Manager):
    """Maintains pending and active action parameters."""

    def __init__(self, agent: object, config: dict, manager_hub: ManagerHub):
        super().__init__(agent, config, manager_hub)
        self.action_params: list[ActionParams] = []  # 暂存当前时刻生成的action参数
        self.actions: dict[str | int, Action] = {}
        # fixme: 处理同一个side，多个agent的情况，id生成器需要区分不同agent
        self.id_generator = make_id_generator(side_name=manager_hub.side)

    def reset(self) -> None:
        self.action_params.clear()
        self.actions.clear()
        self.id_generator.reset()

    def update(self, **kwargs) -> None:
        """action manager 不需要独立维护update"""
        pass

    def step(self) -> list:
        # 添加一个time step累计的所有action到执行
        for action_param in self.action_params:
            self.add_action(action_param)
        self.actions.clear()

        # action step
        commands = []
        for _, action in self.actions.items():
            _, commands_ = action.step()
            commands.extend(commands)

        # 移除运行完成或失败的action
        self.flush_action()
        return commands

    def add_action(self, action_param: ActionParams):
        """构建action实例，并添加到action manager维护"""
        action_id = self.id_generator(action_param.action_type)
        action_param.action_id = action_id
        creator = make_action(action_param.action_type)
        params = {"action_params": action_param.params.copy(), "manager_hub": self.manager_hub}
        class_dict = {"class": creator, "params": params}
        action = construct(class_dict)
        self.actions[action_id] = action

    def record_action(self, action_param: Union[list[ActionParams], ActionParams]) -> None:
        """记录action param"""
        if isinstance(action_param, list):
            self.action_params.extend(action_param)
        elif isinstance(action_param, ActionParams):
            self.action_params.append(action_param)
        else:
            import warnings

            warnings.warn(
                f"Unsupported action params type {type(action_param)}, {action_param}",
                stacklevel=2,
            )
            pass

    def flush_action(self):
        """移除当前时刻不再需要维护的action."""
        non_activate_action_ids = []
        for action_id, action in self.actions.items():
            if action.action_status in [ActionStatus.Exited, ActionStatus.Error]:
                non_activate_action_ids.append(action_id)
        for action_id in non_activate_action_ids:
            del self.actions[action_id]
