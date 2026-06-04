# Forge

`forge` 是一个轻量的 agent-env 开发骨架。当前仓库的重点不是沉淀某个具体仿真环境的业务语义，而是把“业务方案如何变成可运行智能体配置、运行后如何形成报告”这条链路拆出稳定的工程边界。

当前主线示例是 `examples/battle_planner`：基于 LangGraph、LLM agent、本地 planning tools、tick-agent、callback 和 `pysim` 想定，验证从方案规划到仿真反馈的闭环原型。阶段目标和迭代计划见 `forge/docs/roadmap.md`。

## Package Layout

```text
forge/
  core/
    lib/          # 通用 agent、callback、entity、relation、capability、action 抽象
    manager/      # manager hub 与状态/查询管理器骨架
    runtime/      # runner 协议与运行时边界
    specs.py      # 通用 spec/params，如 TickAgentSpec、TickAgentParams、EnvParams
  adapters/       # 外部环境或第三方系统适配，按需求独立演进
  conf/           # 默认配置
  docs/           # forge 自身设计文档
  utils/          # 通用小工具

examples/
  battle_planner/
    adapters/     # battle planner 对外部想定和运行环境的适配
    agents/       # LLM agent：想定理解、方案生成、参数生成、总结
    data/         # 示例 workflow 使用的数据模型，包括 Scheme/Strategy
    evaluation/   # callback 与业务评估组件
    orchestration/# LangGraph workflow、state 和节点
    runtime/      # model provider、middleware、trace、fallback
    tick_agents/  # 业务 tick-agent 及其 TickAgentSpec 声明
    tests/        # 独立 demo 和测试入口

pythonlib/        # 本地仿真/想定依赖，当前作为开发环境输入使用
```

## Boundaries

`forge.core` 只定义通用结构，不放具体业务规划逻辑。

- `forge.core.lib` 保持小而通用，只放基础接口和抽象。
- `forge.core.manager` 负责生命周期、状态维护和查询组织，不沉淀具体场景规则。
- `forge.core.specs` 定义通用 `Spec/Params` 形态。
- `examples/battle_planner` 承载业务 workflow、prompt、策略、指标、实验代码。
- 环境事实以 adapter/runtime 为准，不在 planner 层复制一套仿真合法性引擎。

当前运行层开发形态：

```text
TickAgentSpec   # 描述 tick-agent 能力，给人/LLM/平台看
TickAgentParams # runner 实际执行参数
CallbackParams  # runner 运行时指标采集配置
RunnerReport    # runtime-report 输出
```

当前规划层开发形态：

```text
SchemeSpec   # 上游业务方案输入
StrategySpec # 可审阅的策略卡片
StrategyParams / compiler / tools -> TickAgentParams
```

## Setup

需要 Python 3.13、`uv` 和 `make`。

安装依赖：

```bash
uv sync --all-groups
```

运行基础校验：

```bash
make check
```

只运行核心测试：

```bash
make test
```

运行 battle planner demo：

```bash
make run-battle-planner
```

等价命令：

```bash
PYTHONPATH=.:examples:pythonlib uv run python examples/battle_planner/scripts/run_zc_lite_demo.py
```

## Battle Planner

`examples/battle_planner` 是当前主要实验场。更详细的业务 workflow、agent runtime 和配置说明见：

- `examples/battle_planner/README.md`
- `examples/battle_planner/docs/maritime_scenario.md`

当前 demo 的核心链路是：

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

## Development Notes

- 优先保持小步、可审阅的改动。
- 新业务逻辑优先放在 `examples/battle_planner`，不要下沉到 `forge.core`。
- 新增执行能力时，优先定义 `TickAgentSpec` 和 `TickAgentParams` 边界。
- 新增策略规划能力时，优先定义 `Scheme/Strategy` 数据模型和 tool/compile 边界。
