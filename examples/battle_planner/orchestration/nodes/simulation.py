from __future__ import annotations

from time import perf_counter

from battle_planner.adapters.runtime.runner import Runner
from battle_planner.config import config
from battle_planner.data.models import SimulationRunResult
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.registry import register_battle_planner_modules

from forge.core.specs import CallbackParams, EnvLink, EnvMode, EnvParams


def simulation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "simulation", scenario=state.scenario_name, planned_agents=len(state.planned_agent_params)
    )
    try:
        max_steps = config.simulation.max_decision_steps
        register_battle_planner_modules()
        runner = Runner(
            EnvParams(name="pysim", mode=EnvMode.CREATE, link=EnvLink.GYM),
            tick_agents=state.planned_agent_params,
            callbacks=[
                CallbackParams(
                    name="step_metric",
                    entrypoint="battle_planner.evaluation.callbacks:StepMetricCallback",
                )
            ],
        )
        runner.reset()
        started_at = perf_counter()
        report = runner.run(max_step=max_steps)
        elapsed_seconds = perf_counter() - started_at
        state.simulation_result = SimulationRunResult(
            scenario_name=state.scenario_name,
            steps=report.env.step_count,
            done=report.env.stop_reason == "env_terminal",
            logs=[
                f"reset scenario={state.scenario_name}",
                f"run registered pysim runner max_steps={max_steps} tick_agents={len(state.planned_agent_params)}",
                f"simulation_elapsed_seconds={elapsed_seconds:.4f}",
            ],
            raw_summary={
                "env": "pysim",
                "max_steps": max_steps,
                "tick_agents": [
                    {
                        "agent_instance_id": item.agent_instance_id,
                        "agent_name": item.agent_name,
                    }
                    for item in state.planned_agent_params
                ],
                "elapsed_seconds": elapsed_seconds,
                "runner_report": report.model_dump(),
            },
        )
        state.cur_stage = "simulation"
        log_node_end(
            "simulation",
            steps=state.simulation_result.steps,
            done=state.simulation_result.done,
            env=state.simulation_result.raw_summary.get("env"),
        )
    except Exception as exc:
        state.mark_error(f"simulation failed: {exc}")
        log_node_error("simulation", state.error or str(exc))
    return state
