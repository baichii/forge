## Workspace Scheme

当前仓库采用三层边界：

```text
forge lib               # 通用抽象、协议、基础 agent
forge manager           # hub、manager 基类、4 个 manager
forge adapters          # 外部环境/第三方连接适配
battle_planner          # 业务 planner / prompt / workflow / metrics
```

更细的框架设计见 `forge/docs/architecture.md`。

业务场景设计见 `battle_planner/docs/maritime_scenario.md`。
