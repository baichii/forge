# Forge Architecture

`forge` 的定位是轻量 agent-env 开发骨架，而不是通用业务能力库。

## Boundaries

`forge` 负责定义“怎么问”和“怎么运行”：

- long-lived entity and subordinate entity-reference contracts
- relation and capability query contracts
- planner-facing action intents
- environment-facing action commands
- manager lifecycle
- tick/task agent runtime contracts
- optional orchestration integration wrappers

`manager` 负责定义当前开发主线上的状态维护和查询入口：

- `UnitManager`: long-lived entities and intelligence facts
- `CapabilityManager`: capability judgement
- `RelationManager`: relation and association queries
- `ActionManager`: action lifecycle and pending actions

业务 planner 负责定义“问什么、为什么问、拿结果做什么”：

- prompts
- workflows
- policies
- metrics
- experiments
- scenario-specific optimization logic

## Package Layout

```text
forge/
  lib/           # contracts, dataclasses, and base agents
  manager/       # manager hub, base manager, and concrete managers
  adapters/      # external environment or third-party adapters
  integrations/  # optional orchestration bridges
  conf/          # default config
  docs/          # forge-owned design docs

battle_planner/
  docs/
  workflows/
  prompts/
  policies/
  metrics/
  experiments/
```

## Design Rule

Do not put business planner logic in `forge.core.lib` or `forge.core.manager`.

For example, `attack` can be an action intent or capability label, but the
rules for whether a unit can attack a target belong to `CapabilityManager` and
its supporting managers, not to the entity dataclass itself.

## Current Engineering Notes

`TickAgent` and `TaskAgent` are intentionally separate contracts:

- `TickAgent.step(...)` is for realtime decision loops.
- `TaskAgent.run(...)` is for async task or LLM workflow execution.

`ManagerHub` is the shared lifecycle container for managers. Its input should
converge toward typed observation/entity contracts,
because first-frame global situation and realtime structured updates can have
different shapes.

The framework should support both simulation and non-simulation systems. It
should not assume one universal entity/relation/action semantic model.
