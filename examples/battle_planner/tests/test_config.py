from __future__ import annotations

from battle_planner.conf import HostMode, LLMMode, Settings, SourceMode
from battle_planner.model.options import TaskRunOptions


def test_settings_env_file_does_not_override_existing_env(monkeypatch, tmp_path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("HOST=server\nMODEL=from_file\n", encoding="utf-8")

    monkeypatch.setenv("HOST", "local")
    monkeypatch.setenv("MODEL", "from_runtime")
    settings = Settings(_env_file=env_path)

    assert settings.HOST == HostMode.LOCAL
    assert settings.MODEL == "from_runtime"


def test_settings_parse_runtime_and_model_env(monkeypatch) -> None:
    monkeypatch.setenv("HOST", "server")
    monkeypatch.setenv("SOURCE", "service")
    monkeypatch.setenv("LLM_MODE", "offline")
    monkeypatch.setenv("MODEL", "by_qwen36")
    monkeypatch.setenv("MODEL_PROFILES", "by_qwen36")
    monkeypatch.setenv("MODEL_BY_QWEN36_PROVIDER", "by")
    monkeypatch.setenv("MODEL_BY_QWEN36_API_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("MODEL_BY_QWEN36_API_KEY", "dummy")
    monkeypatch.setenv("MODEL_BY_QWEN36_MODEL_NAME", "test-model")
    monkeypatch.setenv("LLM_MAX_TOKENS", "4096")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("LLM_MAX_RETRY", "3")
    monkeypatch.setenv("SIM_RUNS_PER_PLAN", "5")
    monkeypatch.setenv("SIM_MAX_PARALLEL", "2")
    monkeypatch.setenv("SIM_MAX_DECISION_STEPS", "7")
    monkeypatch.setenv("SIM_MAX_FAILURES", "2")
    monkeypatch.setenv("SIM_RANDOM_SEED", "42")
    monkeypatch.setenv("REPORT_LEVEL", "standard")
    monkeypatch.setenv("REPORT_INCLUDE_LLM_TRACE", "false")

    settings = Settings(_env_file=None)

    assert settings.HOST == HostMode.SERVER
    assert settings.SOURCE == SourceMode.SERVICE
    assert settings.LLM_MODE == LLMMode.OFFLINE
    assert settings.MODEL == "by_qwen36"
    assert settings.LLM_TIMEOUT_SECONDS == 12.5
    assert settings.SIM_MAX_DECISION_STEPS == 7
    assert settings.model_profile_names == ["by_qwen36"]


def test_settings_defaults(monkeypatch) -> None:
    for name in ["HOST", "SOURCE", "LLM_MODE", "MODEL", "MODEL_PROFILES"]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.HOST == HostMode.LOCAL
    assert settings.SOURCE == SourceMode.LOCAL
    assert settings.LLM_MODE == LLMMode.OFFLINE
    assert settings.WORKFLOW_NAME == "zc_lite_baseline"
    assert settings.MODEL == "by_qwen36"
    assert "by_qwen36" in settings.MODEL_PROFILES


def test_task_run_options_defaults_and_explicit_values() -> None:
    options = TaskRunOptions()

    assert options.workflow_name == ""
    assert options.max_iterations == 5
    assert options.sim_runs_per_scheme == 1
    assert options.max_retry == 1

    explicit = TaskRunOptions(
        workflow_name="custom_workflow",
        max_iterations=2,
        sim_runs_per_scheme=5,
        max_retry=3,
        timeout_seconds=60,
        extra={"custom": "value"},
    )

    assert explicit.workflow_name == "custom_workflow"
    assert explicit.max_iterations == 2
    assert explicit.sim_runs_per_scheme == 5
    assert explicit.max_retry == 3
    assert explicit.extra == {"custom": "value"}
