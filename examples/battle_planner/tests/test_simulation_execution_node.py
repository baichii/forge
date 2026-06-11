from __future__ import annotations

from battle_planner.model import TaskRunOptions
from battle_planner.orchestration.state.state import BattlePlannerState

from forge.core.specs import CallbackParams


def test_simulation_execution_node_passes_state_callback_params_to_runner(monkeypatch) -> None:
    import battle_planner.orchestration.nodes.simulation_execution as simulation_module

    captured = _patch_fake_runner(monkeypatch, simulation_module, stop_reason="max_step")
    custom_callback = CallbackParams(
        name="target_statistic",
        callback_instance_id="custom_target_statistic",
        params={
            "side": "red",
            "target_ids": ["red_target_1"],
        },
    )

    result = simulation_module.simulation_execution_node(
        BattlePlannerState(
            scenario_name="zc3_lite",
            callback_params=[custom_callback],
        )
    )

    assert result.simulation_result.done is False
    assert len(result.simulation_results) == 1
    assert result.simulation_results[0].run_index == 0
    assert captured["callbacks"] == [custom_callback]


def test_simulation_execution_node_runs_multiple_simulations(monkeypatch) -> None:
    import battle_planner.orchestration.nodes.simulation_execution as simulation_module

    captured = _patch_fake_runner(monkeypatch, simulation_module, stop_reason="env_terminal")
    custom_callback = CallbackParams(
        name="target_statistic",
        callback_instance_id="custom_target_statistic",
        params={
            "side": "red",
            "target_ids": ["red_target_1"],
        },
    )

    result = simulation_module.simulation_execution_node(
        BattlePlannerState(
            scenario_name="zc3_lite",
            callback_params=[custom_callback],
            task_run_options=TaskRunOptions(sim_runs_per_scheme=2),
        )
    )

    assert len(result.simulation_results) == 2
    assert [item.run_index for item in result.simulation_results] == [0, 1]
    assert result.simulation_result == result.simulation_results[0]
    assert captured["run_count"] == 2


def _patch_fake_runner(monkeypatch, simulation_module, *, stop_reason: str) -> dict:
    captured: dict = {}
    env_stop_reason = stop_reason

    class FakeEnvReport:
        step_count = 3
        stop_reason = env_stop_reason

    class FakeRunnerReport:
        env = FakeEnvReport()

        def model_dump(self):
            return {
                "env": {
                    "step_count": self.env.step_count,
                    "stop_reason": self.env.stop_reason,
                },
                "agents": [],
                "battlefield_events": [],
                "callbacks": {},
            }

    class FakeRunner:
        def __init__(self, *, env, tick_agents, callbacks):
            captured["env"] = env
            captured["tick_agents"] = tick_agents
            captured["callbacks"] = callbacks

        def reset(self):
            captured["reset"] = True

        def run(self, max_step):
            captured["max_step"] = max_step
            captured["run_count"] = captured.get("run_count", 0) + 1
            return FakeRunnerReport()

    monkeypatch.setattr(simulation_module, "register_battle_planner_modules", lambda: None)
    monkeypatch.setattr(simulation_module, "Runner", FakeRunner)
    return captured
