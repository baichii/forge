from typing import Any

from forge.core.specs import CallbackParams


class CallBack:
    """通过回调的形式实现环境态势评估。

    callback 面向业务评估开发者，默认只接收环境态势 observation。
    生命周期 hook 用于记录初始化、结束和 step 级统计，不默认持有 runner。
    """

    def __init__(self, params: CallbackParams):
        self._params = params
        self.params = params.params

    @property
    def name(self):
        """callback 类型名称"""
        return self._params.name

    @property
    def id(self):
        """callback 实例化执行唯一 id"""
        return self._params.callback_instance_id

    def on_begin(self):
        """runner 开始执行后、进入 step 循环前触发一次"""
        ...

    def on_end(self):
        """runner 结束 step 循环后、生成最终 report 前触发一次"""
        ...

    def on_step_begin(self):
        """每个 step 开始前触发，此时本 step 的 env/agent 还未执行"""
        ...

    def on_step_end(self):
        """每个 step 完成后触发，此时 observe 已接收本 step 的 observation"""
        ...

    def observe(self, observation: dict[str, Any]):
        """每个 step 的 env.step 返回 observation 后触发，用于接收当前环境态势"""
        ...

    def result(self):
        """从callback获取事件信息"""
        ...


class CallBackList:
    def __init__(self, callbacks: list):
        self.callbacks = callbacks

    def on_begin(self):
        for callback in self.callbacks:
            callback.on_begin()

    def on_end(self):
        for callback in self.callbacks:
            callback.on_end()

    def on_step_begin(self):
        for callback in self.callbacks:
            callback.on_step_begin()

    def on_step_end(self):
        for callback in self.callbacks:
            callback.on_step_end()

    def observe(self, observation: dict[str, Any]):
        for callback in self.callbacks:
            callback.observe(observation)

    def result(self) -> dict:
        result = {}
        for callback in self.callbacks:
            result[callback.id] = callback.result()
        return result
