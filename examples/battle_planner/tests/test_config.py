from __future__ import annotations

import os


def test_dotenv_does_not_override_existing_env(monkeypatch, tmp_path) -> None:
    from battle_planner.config import load_battle_planner_env

    env_path = tmp_path / ".env"
    env_path.write_text("BATTLE_PLANNER_TEST_PRIORITY=from_dotenv\n", encoding="utf-8")

    monkeypatch.setenv("BATTLE_PLANNER_TEST_PRIORITY", "from_runtime")
    load_battle_planner_env(env_path, override=False)

    assert os.environ["BATTLE_PLANNER_TEST_PRIORITY"] == "from_runtime"


def test_config_groups_parse_env_values(monkeypatch) -> None:
    from battle_planner.config import ModelConfig, ReportConfig, SimulationConfig, WorkflowConfig

    monkeypatch.setenv("BATTLE_PLANNER_MODEL_PROVIDER", "offline")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_MAX_TOKENS", "4096")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_MAX_RETRY", "3")
    monkeypatch.setenv("BATTLE_PLANNER_MAX_STAGE_RETRY", "4")
    monkeypatch.setenv("BATTLE_PLANNER_FAIL_FAST", "true")
    monkeypatch.setenv("BATTLE_PLANNER_SAVE_ARTIFACTS", "false")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_RUNS_PER_PLAN", "5")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_PARALLEL", "2")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_DECISION_STEPS", "7")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_FAILURES", "2")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_RANDOM_SEED", "42")
    monkeypatch.setenv("BATTLE_PLANNER_REPORT_LEVEL", "standard")
    monkeypatch.setenv("BATTLE_PLANNER_REPORT_INCLUDE_LLM_TRACE", "false")

    model = ModelConfig.from_env()
    workflow = WorkflowConfig.from_env()
    simulation = SimulationConfig.from_env()
    report = ReportConfig.from_env()

    assert model.provider == "offline"
    assert model.max_tokens == 4096
    assert model.timeout_seconds == 12.5
    assert model.max_retry == 3
    assert workflow.max_stage_retry == 4
    assert workflow.fail_fast is True
    assert workflow.save_artifacts is False
    assert simulation.runs_per_plan == 5
    assert simulation.max_parallel == 2
    assert simulation.max_decision_steps == 7
    assert simulation.max_failures == 2
    assert simulation.random_seed == 42
    assert report.level == "standard"
    assert report.include_llm_trace is False
