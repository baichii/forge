"""Fake env, tick agent, and runner for battle-planner workflow tests."""

from random import Random
from typing import Any

from battle_planner.data.models import (
    EnvInstance,
    Plan,
    Scenario,
    Strategy,
    TickAgent,
    TickAgentParam,
)


class FakeScenario(Scenario):
    """一个小型、非业务绑定的策略参数测试场景。"""

    name: str
    description: str
    enemy_pressure: float
    terrain_complexity: float
    max_ticks: int = 6


class FakeEnv:
    """Gymnasium-style fake env.

    reset -> (observation, info)
    step -> (observation, reward, terminated, truncated, info)
    """

    def __init__(self, env_instance: EnvInstance):
        self.env_instance = env_instance
        self._rng = Random(env_instance.seed)
        self._sim_time = 0
        self._unit_integrity = 1.0
        self._target_pressure = 0.0

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if seed is not None:
            self.env_instance.seed = seed
        self._rng = Random(self.env_instance.seed)
        self._sim_time = 0
        self._unit_integrity = 1.0
        self._target_pressure = 0.0
        observation = self._build_observation()
        info = {
            "env_type": self.env_instance.env_type,
            "scenario": self.env_instance.scenario.name,
            "options": options or {},
        }
        return observation, info

    def step(
        self,
        action: dict[str, Any],
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        scenario = self.env_instance.scenario
        self._sim_time += 1

        aggression = float(action.get("aggression", 0.5))
        retreat_threshold = float(action.get("retreat_threshold", 0.4))
        formation_gap = float(action.get("formation_gap", 0.5))

        risk = max(0.0, aggression - retreat_threshold)
        risk += scenario.enemy_pressure * 0.12
        risk += self._rng.uniform(-0.08, 0.08)
        risk = max(0.0, risk)

        cohesion = max(0.0, 1.0 - abs(formation_gap - 0.45))
        cohesion -= scenario.terrain_complexity * 0.08
        cohesion += self._rng.uniform(-0.05, 0.05)
        cohesion = max(0.0, min(1.0, cohesion))

        pressure_gain = aggression * 0.62 + cohesion * 0.28 - risk * 0.18
        pressure_gain = max(0.0, min(1.0, pressure_gain))
        damage = max(0.0, risk * 0.12 + scenario.enemy_pressure * 0.02)

        self._target_pressure = max(
            0.0, min(1.0, self._target_pressure + pressure_gain / scenario.max_ticks)
        )
        self._unit_integrity = max(0.0, self._unit_integrity - damage / scenario.max_ticks)

        reward = pressure_gain * 10.0 + cohesion * 3.0 - risk * 5.0
        terminated = self._target_pressure >= 0.92
        truncated = self._sim_time >= scenario.max_ticks
        observation = self._build_observation()
        info = {
            "risk": round(risk, 3),
            "cohesion": round(cohesion, 3),
            "pressure_gain": round(pressure_gain, 3),
            "unit_integrity": round(self._unit_integrity, 3),
            "target_pressure": round(self._target_pressure, 3),
            "event": self._classify_event(risk, cohesion, pressure_gain),
            "action": action,
        }
        return observation, round(reward, 3), terminated, truncated, info

    def _build_observation(self) -> dict[str, Any]:
        return {
            "sim_time": self._sim_time,
            "obs": {
                "unit": {
                    "integrity": round(self._unit_integrity, 3),
                    "position": "friendly_forward_area",
                },
                "target": {
                    "pressure": round(self._target_pressure, 3),
                    "position": "objective_alpha",
                },
                "scenario": {
                    "enemy_pressure": self.env_instance.scenario.enemy_pressure,
                    "terrain_complexity": self.env_instance.scenario.terrain_complexity,
                },
            },
        }

    def _classify_event(self, risk: float, cohesion: float, pressure_gain: float) -> str:
        if risk > 0.42:
            return "overextend"
        if cohesion < 0.86:
            return "formation_drift"
        if pressure_gain < 0.45:
            return "hold_position"
        return "effective_push"


class FakeTickAgent:
    """配置后参与 runner tick 循环的规则智能体。"""

    def __init__(
        self,
        definition: TickAgent,
        *,
        unit_id: str,
        target_id: str,
        params: dict[str, Any],
    ):
        self.definition = definition
        self.unit_id = unit_id
        self.target_id = target_id
        self.params = params

    @property
    def capability_profile(self) -> dict[str, Any]:
        return {
            "name": self.definition.name,
            "description": self.definition.description,
            "function_description": self.definition.function_description,
            "applicable_scenarios": self.definition.applicable_scenarios,
            "params": [param.model_dump() for param in self.definition.params],
        }

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent_name": self.definition.name,
            "unit_id": self.unit_id,
            "target_id": self.target_id,
            "sim_time": observation["sim_time"],
            "aggression": float(self.params.get("aggression", 0.5)),
            "retreat_threshold": float(self.params.get("retreat_threshold", 0.4)),
            "formation_gap": float(self.params.get("formation_gap", 0.5)),
        }


class FakeSimulationRunner:
    """负责启动 env/agent、执行 rollout，并在外部统计指标和关键事件。"""

    def __init__(self, env: FakeEnv, agent: FakeTickAgent):
        self.env = env
        self.agent = agent

    def run(self) -> dict[str, Any]:
        observation, reset_info = self.env.reset()
        logs: list[str] = []
        key_events: list[dict[str, Any]] = []
        rewards: list[float] = []
        step_infos: list[dict[str, Any]] = []

        while True:
            action = self.agent.act(observation)
            observation, reward, terminated, truncated, info = self.env.step(action)
            rewards.append(reward)
            step_infos.append(info)

            event = str(info["event"])
            log = (
                f"t={observation['sim_time']} unit={action['unit_id']} target={action['target_id']} "
                f"event={event} risk={info['risk']} cohesion={info['cohesion']} "
                f"target_pressure={info['target_pressure']} reward={reward}"
            )
            logs.append(log)
            if event in {"overextend", "formation_drift", "effective_push"}:
                key_events.append(
                    {
                        "sim_time": observation["sim_time"],
                        "event": event,
                        "risk": info["risk"],
                        "cohesion": info["cohesion"],
                        "target_pressure": info["target_pressure"],
                    }
                )

            if terminated or truncated:
                break

        statistics = self._build_statistics(rewards, step_infos)
        return {
            "reset_info": reset_info,
            "logs": logs,
            "key_events": key_events,
            "statistics": statistics,
            "score": statistics["score"],
        }

    def _build_statistics(
        self,
        rewards: list[float],
        step_infos: list[dict[str, Any]],
    ) -> dict[str, float | int]:
        avg_risk = sum(float(info["risk"]) for info in step_infos) / len(step_infos)
        avg_cohesion = sum(float(info["cohesion"]) for info in step_infos) / len(step_infos)
        avg_pressure = sum(float(info["pressure_gain"]) for info in step_infos) / len(step_infos)
        final_target_pressure = float(step_infos[-1]["target_pressure"])
        final_unit_integrity = float(step_infos[-1]["unit_integrity"])
        total_reward = sum(rewards)

        score = (
            18.0
            + total_reward * 1.05
            + final_target_pressure * 20.0
            + final_unit_integrity * 12.0
            - avg_risk * 20.0
        )
        score = round(max(0.0, min(100.0, score)), 2)
        return {
            "avg_risk": round(avg_risk, 3),
            "avg_cohesion": round(avg_cohesion, 3),
            "avg_pressure": round(avg_pressure, 3),
            "final_target_pressure": round(final_target_pressure, 3),
            "final_unit_integrity": round(final_unit_integrity, 3),
            "total_reward": round(total_reward, 3),
            "score": score,
            "steps": len(step_infos),
        }


def build_fake_tick_agent_definition() -> TickAgent:
    return TickAgent(
        name="fake_rule_tick_agent",
        description="参数化推进控制智能体，用于小场景策略参数调优流程验证。",
        function_description=(
            "根据 observation 中的 sim_time、unit 状态、target 压制状态，"
            "输出面向指定 unit_id 和 target_id 的推进 action。"
        ),
        applicable_scenarios=[
            "小规模目标压制",
            "规则智能体参数调优",
            "仿真 rollout 骨架验证",
        ],
        version="fake-v1",
        params=[
            TickAgentParam(
                name="unit_id",
                description="执行策略的我方单位 id。",
                type="str",
                default="blue_unit_001",
                examples=["blue_unit_001"],
            ),
            TickAgentParam(
                name="target_id",
                description="策略作用的目标 id。",
                type="str",
                default="red_target_alpha",
                examples=["red_target_alpha"],
            ),
            TickAgentParam(
                name="aggression",
                description="进攻倾向，越高越主动但风险更大。",
                type="float",
                default=0.5,
                min_value=0.0,
                max_value=1.0,
                examples=[0.35, 0.5, 0.75],
            ),
            TickAgentParam(
                name="retreat_threshold",
                description="撤退阈值，越高越保守。",
                type="float",
                default=0.4,
                min_value=0.0,
                max_value=1.0,
                examples=[0.25, 0.4, 0.65],
            ),
            TickAgentParam(
                name="formation_gap",
                description="队形间隔，接近 0.45 时协同效果更稳定。",
                type="float",
                default=0.55,
                min_value=0.0,
                max_value=1.0,
                examples=[0.35, 0.45, 0.7],
            ),
        ],
    )


def build_fake_tick_agent(params: dict[str, Any] | None = None) -> FakeTickAgent:
    definition = build_fake_tick_agent_definition()
    merged_params = {param.name: param.default for param in definition.params}
    if params:
        merged_params.update(params)
    return FakeTickAgent(
        definition,
        unit_id=str(merged_params["unit_id"]),
        target_id=str(merged_params["target_id"]),
        params=merged_params,
    )


def build_fake_scenario(seed: int = 7) -> EnvInstance:
    scenario = FakeScenario(
        name="fake_small_battle",
        description="一个只用于流程验证的小场景：高压敌情、有限地形复杂度。",
        enemy_pressure=0.62,
        terrain_complexity=0.35,
        max_ticks=6,
    )
    return EnvInstance(env_type="fake", scenario=scenario, seed=seed)


def build_existing_strategy() -> Strategy:
    return Strategy(
        name="baseline_pressure_control",
        description="已有策略：保持稳定队形，在敌方压力升高时降低风险并维持有限推进。",
        source=build_fake_tick_agent_definition(),
    )


def build_existing_plan() -> Plan:
    return Plan(
        name="fake_parameter_optimization_plan",
        description="对已有规则智能体策略做三轮参数填充、仿真和反馈优化。",
        plan_branches=[],
    )
