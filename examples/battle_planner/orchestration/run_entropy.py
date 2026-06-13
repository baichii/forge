"""Run 级 workflow 执行入口。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from battle_planner.conf import settings
from battle_planner.model import RunIterationOutputSpec, TaskRunSpec
from battle_planner.orchestration.history import build_history_item
from battle_planner.orchestration.output import build_run_iteration_output
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import build_initial_state
from battle_planner.orchestration.workflow_stream import WorkflowStreamService


@dataclass
class RunEntropyError(RuntimeError):
    """RunEntropy 执行过程中产生的 workflow 错误。"""

    reason: str
    message: str
    last_iteration_index: int | None = None

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.message)


class RunEntropy:
    """对外暴露的 run 级 workflow 入口。"""

    def __init__(
        self,
        *,
        workflow_name: str | None = None,
        verbose: int | None = None,
        print_events: bool = False,
    ):
        self.workflow_name = workflow_name
        self.verbose = settings.VERBOSE if verbose is None else verbose
        self.print_events = print_events

    def run_iterations(self, task_run: TaskRunSpec) -> Iterator[RunIterationOutputSpec]:
        """执行 TaskRunSpec 并逐轮产出运行结果。

        Args:
            task_run: 本次任务运行输入。

        Yields:
            每一轮 workflow 执行后的输出摘要。

        Raises:
            RunEntropyError: workflow state 标记失败时抛出。
        """

        history: list[dict] = []
        workflow_name = self.workflow_name or task_run.options.workflow_name or None
        stream_service = WorkflowStreamService(workflow_name=workflow_name)

        for iteration_index in range(task_run.options.max_iterations):
            initial_state = build_initial_state(task_run).model_copy(
                update={
                    "iteration_index": iteration_index,
                    "history": list(history),
                    "verbose": self.verbose,
                }
            )
            stream_result = stream_service.stream(initial_state, print_events=self.print_events)
            state = stream_result.final_state
            yield build_run_iteration_output(state)

            if state.error:
                raise RunEntropyError(
                    reason="workflow_state_error",
                    message=state.error,
                    last_iteration_index=state.iteration_index,
                )
            if state.cur_stage == WorkflowStages.COMPLETE:
                history.append(build_history_item(state))
