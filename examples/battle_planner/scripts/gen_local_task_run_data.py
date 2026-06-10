"""生成workflow入口参数

Notes:
    1. 主要用于本地运行

"""

import json

from battle_planner.workspace.local.run_input_seed import build_local_task_run


def gen_local_task_run_spec() -> dict:
    """生成 workflow 可直接使用的 TaskRunSpec。"""

    return build_local_task_run().model_dump(mode="json")


if __name__ == "__main__":
    print(json.dumps(gen_local_task_run_spec(), ensure_ascii=False, indent=2))
