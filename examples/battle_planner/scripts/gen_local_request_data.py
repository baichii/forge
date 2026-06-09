"""生成模拟前端/本地入口请求数据。"""

from battle_planner.model.requests import (
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
)
from battle_planner.model.workflow import HumanInputSpec


def generate_local_task_context_request() -> dict:
    """生成创建 TaskContext 的本地请求。"""

    request = TaskContextCreateRequest(
        plan_id="2175313467819556864",
        name="航母对抗任务上下文001",
        plan_human=HumanInputSpec(
            summary="人工希望先验证任务方案、策略迭代和推演配置的数据链路。",
            items=[
                "当前只保留一个策略分支，不考虑备选方案对比。",
                "只评价该策略是否完成摧毁航母目标。",
            ],
        ),
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id="branch-carrier-strike-validation",
                human=HumanInputSpec(
                    summary="人工确认本轮只做单分支验证。",
                    items=[
                        "不要同时优化对手策略。",
                        "武器数量先保守，后续根据仿真反馈调整。",
                    ],
                ),
            )
        ],
    )
    return request.model_dump(mode="json")


def generate_local_task_run_request() -> dict:
    """生成创建 TaskRun 的本地请求。"""

    request = TaskRunCreateRequest(
        task_context_id="task-context-local-001",
        run_name="航母对抗策略迭代运行001",
        options={
            "workflow_name": "zc_lite_baseline",
            "max_iterations": 5,
            "sim_runs_per_scheme": 1,
            "max_retry": 1,
            "timeout_seconds": None,
            "extra": {},
        },
    )
    return request.model_dump(mode="json")


if __name__ == "__main__":
    print(generate_local_task_context_request())
    print(generate_local_task_run_request())
