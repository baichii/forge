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
    runtime/         # 外部想定和环境适配，包含 scenario_zc_lite 加载、pysim factory 和 runner
  data/              # demo workflow 使用的 Pydantic 数据模型
  evaluation/        # 业务评估和指标采集组件；首版指标为占位/随机
  orchestration/     # LangGraph workflow、state 和节点
  agents/            # LLM agent：想定理解、方案生成、参数生成、总结
    context/          # LLM agent 输入上下文：知识包构造和工具说明
  runtime/           # model provider、middleware、fallback 和 trace 记录
  tick_agents/       # 项目业务 tick agent、declaration 和 schema 加载入口
  workspace/         # 本地复现工作区：source 存放外部资源快照，artifacts 存放运行产物
  tests/             # 测试用例和可直接运行的 demo 验证入口
```

## Workflow

```text
prepare_scenario
 -> scenario_understanding
 -> battle_plan_generation
 -> agent_schema_loading
 -> agent_parameter_planning
 -> simulation
 -> evaluation
 -> summary
```

`prepare_scenario` 会把 `scenario_zc_lite` 转成 `PlannerKnowledgePack`，其中包含想定摘要、作战目标、可用智能体能力、mission schema、约束、未知项和证据来源。后续 `scenario_understanding` 与 `battle_plan_generation` 都基于这个知识包工作。

每个 LLM 环节都会记录 trace，包括输入消息、原始输出、解析结果、fallback 状态和错误信息。Markdown 生成环节在模型不可用时会使用模板兜底；智能体参数生成失败时不再自动补默认 agent，`planned_agent_params` 会保持为空，方便定位问题。

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

模型调用通过 `runtime/model_provider.py` 抽象。`.env` 中通过 `MODEL` 显式选择模型 profile，不再自动选择。默认使用 `MODEL=deepseek_v4_pro`：

- `MODEL=deepseek_v4_pro`：使用 `MODEL_DEEPSEEK_V4_PRO_*`，并启用 `reasoning_effort=high` 和 `thinking.type=enabled`
- `MODEL=openai_gpt54_mini`：使用 `MODEL_OPENAI_GPT54_MINI_*`
- `MODEL=local_qwen36`：使用 `MODEL_LOCAL_QWEN36_*`
- `MODEL=offline`：不请求模型，直接走 fallback

agent 调用可传入 `model` 参数；如果传入值和当前 profile 的 `MODEL_NAME` 不一致，会直接返回配置错误，避免测试时误用模型。

`display-mode` 可用于演示和 K3 闭环调试：设置 `BATTLE_PLANNER_DISPLAY_MODE=true` 后，想定理解、方案生成和总结仍由 LLM 生成，但 agent runtime 参数会从 `workspace/local/runtime_presets/` 中按 `iteration_index` 读取，避免弱模型生成不存在的单位 id。这个能力是临时演示开关。

运行配置集中在 `config.py`。配置优先级为：

```text
容器/系统环境变量 > examples/battle_planner/.env > config.py 默认值
```

`.env.example` 按 `API / Model / Workflow / Simulation / Report` 分组列出可调参数。本地调试可复制为 `.env`，容器化部署时建议通过启动环境变量传入参数。
