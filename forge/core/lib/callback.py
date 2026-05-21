from typing import Protocol

from forge.core.specs import CallbackParams


class CallBack:
    """通过回调的形式来实现指标评估"""

    def __init__(self, params: CallbackParams):
        self._runner = None
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

    def set_runner(self, runner):
        # Note: runner在这里临时充当manager hub的能力，但态势封装会带来高昂的学习成本
        # todo: 确定最终方案
        self._runner = runner

    def on_begin(self): ...

    def on_end(self): ...

    def on_step_begin(self): ...

    def on_step_end(self): ...

    def result(self):
        """从callback获取事件信息"""
        ...


class CallBackList:
    def __init__(self, callbacks: list):
        self.callbacks = callbacks

    def set_runner(self, runner):
        for callback in self.callbacks:
            callback.set_runner(runner)

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

    def result(self) -> dict:
        result = {}
        for callback in self.callbacks:
            result[callback.id] = callback.result()
        return result
