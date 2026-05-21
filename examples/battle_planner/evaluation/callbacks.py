from __future__ import annotations

from typing import Any

from forge.core.lib.callback import CallBack
from forge.core.specs import CallbackParams


class StepMetricCallback(CallBack):
    """Minimal runtime metric callback for runner smoke validation."""

    def __init__(self, params: CallbackParams):
        super().__init__(params=params)
        self.run_begin_count = 0
        self.run_end_count = 0
        self.step_begin_count = 0
        self.step_end_count = 0

    def on_begin(self) -> None:
        self.run_begin_count += 1

    def on_end(self) -> None:
        self.run_end_count += 1

    def on_step_begin(self) -> None:
        self.step_begin_count += 1

    def on_step_end(self) -> None:
        self.step_end_count += 1

    def result(self) -> dict[str, Any]:
        return {
            "run_begin_count": self.run_begin_count,
            "run_end_count": self.run_end_count,
            "step_begin_count": self.step_begin_count,
            "step_end_count": self.step_end_count,
        }


class KeyTargetDestroy(CallBack):
    def __init__(self, params: CallbackParams):
        super().__init__(params=params)
        self._target_ids = self.params["target_ids"]
        self._result = {}

    def on_begin(self):
        pass

    def result(self):
        return self._result
