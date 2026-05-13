import traceback

from battle_planner.data.models import Plan, PlanBranch,Strategy, PlanExecuteResult


class BattlePlannerWorkflow:
    """
    测试工作流

    Notes:
        1. 大幅简化场景, plan-> plan branch -> strategy 的流程直接优化为对策略进行优化
        2. langgraph-node部分节点先硬编码跑通流程

    """

    def __init__(self):
        pass


