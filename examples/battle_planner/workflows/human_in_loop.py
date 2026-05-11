"""一个简单的human in loop demo"""
from idlelib import config
from typing import TypedDict
from unittest import result

from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver


class State(BaseModel):
    user_input: str
    plan: str | None = None
    approved: bool | None = None
    result: str | None = None


def plan_node(state: State):
    """生成计划"""
    user_input = state.user_input
    plan = f"执行任务: {user_input}"

    print(f"生成计划: {plan}")

    return {"plan": plan}


def human_review_node(state: State):
    print("审核节点")

    approved = interrupt(
        "是否批准？ 输入 1/0"
    )
    print(f"审核结构: {type(approved)}, {approved}")
    return {"approved": approved == "1"}


def execute_node(state: State):
    print("执行节点")

    if not state.approved:
        result = "审核失败"
    else:
        result = f"开始执行 {state.plan}"
    print("res: ", result)
    return {
        "result": result
    }


def build_graph():
    builder = StateGraph(State)

    builder.add_node("plan", plan_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("execute", execute_node)

    builder.set_entry_point("plan")
    builder.add_edge("plan", "human_review")
    builder.add_edge("human_review", "execute")
    builder.add_edge("execute", END)

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph


def main():
    initial_state = State(
        user_input="hello world"
    )

    graph = build_graph()
    config = {
        "configurable": {
            "thread_id": "user_1"
        }
    }
    result = graph.invoke(initial_state, config=config)

    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0]

        print("等待审核: \n")
        print(interrupt_info.value)

        user_approval = input("输入 1 or 0")
        print("输入结果: ", user_approval)
        resumed_result= graph.invoke(
            Command(resume=user_approval), config=config
        )

        print("\n 结果")
        print(resumed_result)


if __name__ == '__main__':
    main()

