from __future__ import annotations

from time import perf_counter

from battle_planner.adapters.runtime.runner import Runner
from battle_planner.conf import settings
from battle_planner.model import SimulationRunResult
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.registry import register_battle_planner_modules

from forge.core.specs import EnvLink, EnvMode, EnvParams


def simulation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "simulation",
        iteration_index=state.iteration_index,
        scenario=state.scenario_name,
        planned_agents=len(state.planned_agent_params),
    )
    try:
        if not state.callback_params:
            raise ValueError("simulation requires callback_params from scenario runtime config")
        max_steps = settings.SIM_MAX_DECISION_STEPS
        register_battle_planner_modules()
        runner = Runner(
            env=EnvParams(
                name="pysim",
                mode=EnvMode.CREATE,
                link=EnvLink.GYM,
                params={"scenario_name": state.scenario_name or "zc_lite", "render_mode": "none"},
            ),
            tick_agents=state.planned_agent_params,
            callbacks=state.callback_params,
        )
        runner.reset()
        started_at = perf_counter()
        report = runner.run(max_step=max_steps)
        elapsed_seconds = perf_counter() - started_at
        stop_reason = report.env.stop_reason
        state.simulation_result = SimulationRunResult(
            scenario_name=state.scenario_name,
            steps=report.env.step_count,
            done=_is_env_finished(stop_reason),
            logs=[
                f"reset scenario={state.scenario_name}",
                f"run registered pysim runner max_steps={max_steps} tick_agents={len(state.planned_agent_params)}",
                f"stop_reason={stop_reason}",
                f"simulation_elapsed_seconds={elapsed_seconds:.4f}",
            ],
            raw_summary={
                "env": "pysim",
                "max_steps": max_steps,
                "stop_reason": stop_reason,
                "tick_agents": [
                    {
                        "agent_instance_id": item.agent_instance_id,
                        "agent_name": item.agent_name,
                        "side": item.side,
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
            iteration_index=state.iteration_index,
            steps=state.simulation_result.steps,
            done=state.simulation_result.done,
            stop_reason=stop_reason,
            env=state.simulation_result.raw_summary.get("env"),
        )
    except Exception as exc:
        state.mark_error(f"simulation failed: {exc}")
        log_node_error("simulation", state.error or str(exc), iteration_index=state.iteration_index)
    return state


def _is_env_finished(stop_reason: str) -> bool:
    return stop_reason in {"env_terminal", "env_truncated"}
