from __future__ import annotations

import copy
from typing import Any

from battle_planner.adapters.scenario_loader import ensure_pythonlib_path
from battle_planner.data.demo_models import PlannedAgentParams, SimulationRunResult


def _get_planned_params(
    planned_agent_params: list[PlannedAgentParams],
    agent_name: str,
) -> dict[str, Any]:
    for item in planned_agent_params:
        if item.agent_name == agent_name:
            return item.params
    return {}


def _build_blue_rule_agent(planned_agent_params: list[PlannedAgentParams]):
    ensure_pythonlib_path()
    from example_zc.agent.agent import DispatcherAgent
    from example_zc.mission.mission.mission import MissionType

    strike_params = _get_planned_params(planned_agent_params, "strike_planner")
    timing_params = _get_planned_params(planned_agent_params, "mission_timing_planner")

    activation_time = int(timing_params.get("activation_time", 120))
    target_ids = strike_params.get("target_ids") or ["red_CV16 “辽宁”号001型航空母舰_1"]
    unit_ids = strike_params.get("unit_ids") or [
        "blue_F/A-18F型“超级大黄蜂”战斗机_14",
        "blue_F/A-18F型“超级大黄蜂”战斗机_15",
        "blue_F/A-18F型“超级大黄蜂”战斗机_16",
        "blue_F/A-18F型“超级大黄蜂”战斗机_17",
    ]
    wp_nums = strike_params.get("wp_nums") or [int(strike_params.get("weapon_per_target", 4))]

    class BlueDemoRuleAgent(DispatcherAgent):
        manual_mission_dicts = [
            {
                "activation_time": activation_time,
                "type": MissionType.NavalAsuWStrike_Air,
                "unit_ids": unit_ids,
                "target_ids": target_ids,
                "wp_nums": wp_nums,
                "clear_targets": True,
            }
        ]

    return BlueDemoRuleAgent


def _build_agent_conf(planned_agent_params: list[PlannedAgentParams]) -> list[dict[str, Any]]:
    ensure_pythonlib_path()
    from example_zc.agent.agent import Agent
    from example_zc.agent.zc3.blue_agent import agent_conf as default_blue_agent_conf
    from example_zc.agent.zc3.const import Const
    from example_zc.training.agent import ControlType

    blue_agent_conf = copy.deepcopy(default_blue_agent_conf)
    blue_agent_conf["use_model"] = False
    blue_agent_conf["use_rule"] = True
    blue_agent_conf["rule_conf"] = {
        "agent_class": _build_blue_rule_agent(planned_agent_params),
        "params": {},
    }

    red_agent_conf = copy.deepcopy(default_blue_agent_conf)
    red_agent_conf["name"] = "red"
    red_agent_conf["use_model"] = False
    red_agent_conf["use_rule"] = False

    return [
        {
            "side": "red",
            "agent_class": Agent,
            "control_mode": ControlType.Command,
            "params": {"agent_conf": red_agent_conf},
        },
        {
            "side": "blue",
            "agent_class": Agent,
            "control_mode": ControlType.Command,
            "params": {"agent_conf": blue_agent_conf},
        },
    ]


def run_zc_lite_drill_env(
    scenario_conf: dict[str, Any],
    planned_agent_params: list[PlannedAgentParams],
    *,
    max_decision_steps: int = 3,
) -> SimulationRunResult:
    ensure_pythonlib_path()
    from pysim.constants import CONSTANTS

    CONSTANTS.set_constant("RENDER_MODE", "")
    try:
        from example_zc.agent.zc3.const import Const
        from example_zc.training.drill_env import DrillEnv
    except ModuleNotFoundError as exc:
        if exc.name != "drill":
            raise
        return run_zc_lite_sim_fallback(
            scenario_conf,
            max_steps=max_decision_steps,
            fallback_reason="DrillEnv requires external package `drill`; used pysim.Sim fallback.",
        )

    training_conf = {
        "training_side": "blue",
        "model_command_interval": Const.BlueCommandInterval["model"],
    }
    env = DrillEnv(0, scenario_conf, _build_agent_conf(planned_agent_params), training_conf)
    env.reset()

    logs: list[str] = [f"reset scenario={scenario_conf['name']}"]
    done = False
    steps = 0
    last_obs_keys: list[str] = []
    for step_index in range(max_decision_steps):
        obs, done = env.step(command_dict={scenario_conf["name"]: {"missions": []}})
        steps = step_index + 1
        last_obs_keys = list(obs.keys())
        logs.append(f"decision_step={steps} done={done} obs_keys={last_obs_keys}")
        if done:
            break

    return SimulationRunResult(
        scenario_name=scenario_conf["name"],
        steps=steps,
        done=done,
        logs=logs,
        raw_summary={
            "env": "DrillEnv",
            "max_decision_steps": max_decision_steps,
            "last_obs_keys": last_obs_keys,
        },
    )


def run_zc_lite_sim_fallback(
    scenario_conf: dict[str, Any],
    *,
    max_steps: int,
    fallback_reason: str,
) -> SimulationRunResult:
    """Run the real pysim core when example_zc DrillEnv dependencies are absent."""
    ensure_pythonlib_path()
    from pysim import Sim
    from pysim.constants import CONSTANTS

    CONSTANTS.set_constant("RENDER_MODE", "")
    env = Sim(scenario_conf, subscribe_cont=True, render_mode="")
    env.reset(scenario_conf["units"])
    logs = [fallback_reason, f"reset scenario={scenario_conf['name']} with pysim.Sim"]
    done = False
    for step_index in range(max_steps):
        _, _, terminated, truncated, info = env.step(action=[])
        done = bool(terminated or truncated)
        logs.append(
            f"sim_step={step_index + 1} done={done} damage_keys={list(info.get('damage', {}).keys())}"
        )
        if done:
            break

    return SimulationRunResult(
        scenario_name=scenario_conf["name"],
        steps=max_steps,
        done=done,
        logs=logs,
        raw_summary={
            "env": "pysim.Sim",
            "fallback_reason": fallback_reason,
            "max_steps": max_steps,
        },
    )
