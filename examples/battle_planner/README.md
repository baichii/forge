# Battle Planner

`battle_planner` 是一个垂直 demo，用来验证“想定理解 -> 方案生成 -> 智能体参数生成 -> 真实环境推演 -> 独立评估 -> 总结”的端到端流程。

当前目标是先跑通整体链路和可观察输入输出，不追求方案效果。业务逻辑、prompt、workflow、指标和实验代码都放在这里，不放入 `forge.lib` 或 `forge.manager`。

## Run

```bash
uv run python examples/battle_planner/tests/run_zc_lite_demo.py
```

当前测试环境通过 battle-planner 本地 registry 构造 `pysim` 环境，并由 runner 驱动有限步推演。

## Directory

```text
examples/battle_planner/
  adapters/          # 外部想定和环境适配，包含 scenario_zc_lite 加载、pysim factory 和 runner
  data/              # demo workflow 使用的 Pydantic 数据模型
  evaluation/        # 独立评估组件；首版指标为占位/随机
  knowledge/          # 想定 + 环境知识 -> PlannerKnowledgePack
  orchestration/     # LangGraph workflow、state 和节点
  planning/          # LLM 规划环节：想定理解、方案生成、参数生成、总结
  runtime/           # model provider、middleware、fallback 和 trace 记录
  tick_agents/       # 可实时运行的 tick agent 示例、declaration 和 schema 加载入口
  tools/             # 首版本地查询工具描述，占位替代 forge manager 能力
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

每个 LLM 环节都会记录 trace，包括输入消息、原始输出、解析结果、fallback 状态和错误信息。模型不可用或输出不适合展示时，demo 会使用模板或默认参数继续跑完。

## Agent Runtime

`planning` 中的每个规划环节都由 `BasePlanningAgent` 派生：

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

模型调用通过 `runtime/model_provider.py` 抽象。`.env` 中的 `BATTLE_PLANNER_MODEL_PROVIDER` 支持：

- `auto`：优先 local，其次 openai，最后 offline
- `local`：使用 `LOCAL_OPENAI_*`
- `openai`：使用 `OPENAI_*`
- `offline`：不请求模型，直接走 fallback

运行配置集中在 `config.py`。配置优先级为：

```text
容器/系统环境变量 > examples/battle_planner/.env > config.py 默认值
```

`.env.example` 按 `API / Model / Workflow / Simulation / Report` 分组列出可调参数。本地调试可复制为 `.env`，容器化部署时建议通过启动环境变量传入参数。
