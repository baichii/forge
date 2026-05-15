
## 需求

`forge` 是一个轻量 agent-env 开发骨架。核心目标不是沉淀具体环境的业务语义，而是约定一套稳定的开发调用结构：

```text
observe -> normalize -> query/reason -> plan -> translate -> act -> update
```

核心边界：

- `forge.lib`: 实体、关系、能力、动作抽象，以及基础 agent 定义。
- `forge.manager`: `ManagerHub`、`Manager` 基类，以及 Unit/Capability/Relation/Action 四个 manager。
- `forge.adapters`: 外部环境或第三方连接适配。
- `forge.integrations`: LangGraph、openai-agents 等可选编排集成。
- `battle_planner`: 基于 forge manager/lib 的业务 planner，不进入 forge 基础层。

安装依赖时使用：

```bash
uv sync --all-groups
```
