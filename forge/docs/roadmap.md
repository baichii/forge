# Forge Roadmap

当前开发围绕 `examples/battle_planner` 推进，目标是在小型航母编队作战场景中跑通“方案规划 -> 仿真运行 -> 报告反馈 -> 方案迭代”的最小闭环。



## K1: 仿真 -> 运行时报告

K1 关注循环 `2 -> 3`：给定可执行配置，运行仿真并生成 runtime-report。

核心组件：

- 基础 tick-agent
- 事件收集
- callback
- runner report

当前目标：

- 在 `zc_lite` 场景中构建 2 个具有差异的方案。
- 运行后能输出有差异的 runtime-report。
- 报告能够支撑后续方案迭代，例如目标是否存活、血量变化、关键事件和 agent 执行动作。

当前状态：

- 已形成 `TickAgentSpec -> TickAgentParams -> runner -> CallbackParams -> RunnerReport` 的基础开发形态。
- 已有空对海、舰对海 tick-agent。
- 已有 `TargetStatistic` 等 runtime callback。



## K2: 业务方案 -> tick-agent 配置

K2 关注循环 `1 -> 2`：把上游业务方案转成 runner 可执行的 tick-agent 配置。

核心问题：

- 约束构建：定义足够清晰的前置约束和优化目标。
- LLM 支持：agent 可以获取想定、智能体描述和可用能力信息。
- tool-call：以工具接口查询想定、目标、候选单位、tick-agent 能力和编译结果。
- 抽象建设：像 K1 定义 tick-agent/callback 开发形态一样，定义 K2 的 Scheme/Strategy/tool/compiler 开发形态。

当前收敛方向：

```text
SchemeSpec
 -> StrategySpec
 -> planning tools / compiler
 -> TickAgentParams
 -> K1 runner
 -> runtime-report
```

设计边界：

- `SchemeSpec` 承接上游业务输入，描述方案目标、约束和策略卡片集合。
- `StrategySpec` 表达可审阅的策略卡片，先保持最小字段，等 demo 跑通后再扩展。
- tool-call 作为功能接口建设，但第一阶段可以先接本地 tool backend。
- 不在 K2 早期做复杂合法性校验，优先稳定模型、接口和测试脚本。





## K3: 方案迭代

K3 关注大循环：`K2 -> K1 -> K2 -> K1 ...`。

目标：

- 在约束条件下形成方案迭代。
- 比较不同策略方案的 runtime-report。
- 根据目标状态、指标变化和运行事件调整下一轮策略。
- 构建简单 Web UI，支持查看过程调用、生成的方案、runtime-report 和指标变化。

K3 暂不提前展开复杂实现，等 K1/K2 的数据边界稳定后再进入。
