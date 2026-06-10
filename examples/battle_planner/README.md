# Battle Planner

`battle_planner` 是一个垂直 demo，用来验证“想定理解 -> 方案生成 -> 智能体参数生成 -> 真实环境推演 -> 独立评估 -> 总结”的端到端流程。

当前目标是先跑通整体链路和可观察输入输出，不追求方案效果。业务逻辑、prompt、workflow、指标和实验代码都放在这里，不放入 `forge.core.lib` 或 `forge.core.manager`。

## Run

```bash
PYTHONPATH=.:examples:pythonlib uv run python examples/battle_planner/scripts/run_zc_lite_demo.py
```

当前测试环境通过 battle-planner 本地 registry 构造 `pysim` 环境，并由 runner 驱动有限步推演。

## Directory

```text
examples/battle_planner/
  adapters/          # 对齐 forge.core 的项目适配层，不放业务策略
    runtime/         # 外部想定和环境适配，包含 scenario 加载、pysim factory 和 runner
  model/             # source/request/task/scheme/deduction 等 Pydantic 数据模型
  orchestration/     # LangGraph workflow、state、nodes、pipeline 和业务评估逻辑
  agents/            # LLM agent：想定理解、方案生成、参数生成、总结
    context/          # LLM agent 输入上下文：知识包构造和工具说明
  llm_runtime/       # model provider、middleware 和 trace 记录
  workspace/         # 本地复现工作区：local 存放 demo seed/source，resource 存放拉取资源
  scripts/           # 本地数据生成、resource config 导出等薄脚本入口
  experimental/      # 临时实验和运行产物，不作为稳定接口
  tests/             # 最小离线可维护测试套件
  ui/                # 临时演示 UI，当前冻结扩张
```

## Workflow

```text
scenario_preparation
 -> scenario_understanding
 -> battle_plan_generation
 -> agent_schema_loading
 -> agent_parameter_planning
 -> simulation_execution
 -> result_evaluation
 -> summary_generation
```

`scenario_preparation` 会把 `scenario_zc_lite` 转成 `PlannerKnowledgePack`，其中包含想定摘要、作战目标、可用智能体能力、mission schema、约束、未知项和证据来源。后续 `scenario_understanding` 与 `battle_plan_generation` 都基于这个知识包工作。

每个 LLM 环节都会记录 trace，包括输入消息、原始输出、解析结果和错误信息。`LLM_MODE=offline` 时节点直接读取 `run_output_seed`，不会创建模型 provider，也不会触发 fallback；live 模型失败和校验重试策略后续再进入前端错误处理链路。

## Agent Runtime

`agents` 中的每个 LLM agent 都由 `BasePlanningAgent` 派生：

- `ScenarioUnderstandingAgent`
- `BattlePlanGenerationAgent`
- `AgentParameterPlanningAgent`
- `SummaryAgent`

agent 输入统一支持：

- `tools`：当前可用工具或工具说明
- `memory`：历史上下文或摘要
- `skills`：指导 agent 如何完成任务的技能说明

`runtime/middleware.py` 预留了类似 deepagents 的 middleware 栈。当前默认启用：

- `InputContextMiddleware`：把 tool、memory、skill 注入模型上下文
- `TraceMetadataMiddleware`：记录 middleware hook 和输出摘要

模型调用通过 `llm_runtime/model_provider.py` 抽象。`.env` 中通过 `LLM_MODE` 控制是否真实调用模型，并通过 `MODEL` 显式选择模型 profile。默认使用 `LLM_MODE=offline` 和 `MODEL=by_qwen36`：

- `LLM_MODE=offline`：不请求模型，LLM 节点从 `workspace/local/run_output_seed.py` 读取本地产物
- `LLM_MODE=live`：按 `MODEL` 选择的 profile 请求真实模型
- `MODEL=by_qwen36`：使用 `MODEL_BY_QWEN36_*`
- `MODEL=openai_gpt54_mini`：使用 `MODEL_OPENAI_GPT54_MINI_*`
- `MODEL=deepseek_v4_pro`：使用 `MODEL_DEEPSEEK_V4_PRO_*`

agent 调用可传入 `model` 参数；如果传入值和当前 profile 的 `MODEL_NAME` 不一致，会直接返回配置错误，避免测试时误用模型。

运行配置集中在 `conf.py`。配置优先级为：

```text
容器/系统环境变量 > examples/battle_planner/.env > conf.py 默认值
```

`.env.example` 列出本地调试常用参数。本地调试可复制为 `.env`，容器化部署时建议通过启动环境变量传入参数。

## Tests

`examples/battle_planner/tests` 只维护最小离线测试套件。默认测试必须在断网、`LLM_MODE=offline`、不依赖真实模型服务的情况下通过。

测试维护原则：

- 测试只覆盖关键模块边界和主数据流，例如本地 seed 装配、resource 加载、核心 node、runner smoke 和 workflow smoke。
- 不在 pytest 中维护 live model 连接探针、手动展示脚本或大段 payload 打印。
- 不用大量断言复述 Pydantic 字段定义；优先验证“这个模块边界坏了是否能被发现”。
- 不在测试文件中保留 `print(...)`、`if __name__ == "__main__"` 或需要人工观察输出的入口。
- 需要真实 LLM、复杂演示或人工观察输出时，另开临时脚本，不进入 pytest 主套件。

推荐验证命令：

```bash
PYTHONPATH=.:examples:pythonlib uv run pytest examples/battle_planner/tests -q
PYTHONPATH=.:examples:pythonlib uv run ruff check examples/battle_planner
PYTHONPATH=.:examples:pythonlib uv run ruff format --check examples/battle_planner
```
