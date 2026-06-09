"""生成模拟前端/本地入口请求数据。"""

import json

from battle_planner.workspace.local.demo_seed import (
    build_local_task_context_request,
    build_local_task_run_request,
)


def generate_local_task_context_request() -> dict:
    """生成创建 TaskContext 的本地请求。"""

    return build_local_task_context_request().model_dump(mode="json")


def generate_local_task_run_request() -> dict:
    """生成创建 TaskRun 的本地请求。"""

    return build_local_task_run_request().model_dump(mode="json")


if __name__ == "__main__":
    print(json.dumps(generate_local_task_context_request(), ensure_ascii=False, indent=2))
    print(json.dumps(generate_local_task_run_request(), ensure_ascii=False, indent=2))
