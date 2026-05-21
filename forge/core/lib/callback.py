from typing import Protocol


class CallBack(Protocol):
    """通过回调的形式来实现指标评估"""

    name = "base_callback"

    def __init__(self, *args, **kwargs):
        self._runner = None

    def set_runner(self, runner):
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
            result[callback.name] = callback.result()
        return result
