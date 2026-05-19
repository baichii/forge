from __future__ import annotations

from typing import Any


class StepMetricCallback:
    """Minimal runtime metric callback for runner smoke validation."""

    def __init__(self, name: str = "step_metric", **kwargs: Any):
        self.name = name
        self.params = kwargs
        self._runner = None
        self.run_begin_count = 0
        self.run_end_count = 0
        self.step_begin_count = 0
        self.step_end_count = 0

    def set_runner(self, runner) -> None:
        self._runner = runner

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
