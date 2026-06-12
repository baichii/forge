from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from battle_planner.model import SchemeBranchExecutionSpec

from forge.core.specs import TickAgentParams

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
AGENT_PARAM_PRESET_FILE = (
    BATTLE_PLANNER_ROOT / "workspace" / "local" / "runtime_presets" / "zc3_lite_agent_params.json"
)
LEGACY_AGENT_PARAM_PRESET_FILE = BATTLE_PLANNER_ROOT / "runtime" / "presets" / "zc3_lite_agent_params.json"


def resolve_agent_param_preset_file() -> Path:
    if AGENT_PARAM_PRESET_FILE.exists() or not LEGACY_AGENT_PARAM_PRESET_FILE.exists():
        return AGENT_PARAM_PRESET_FILE
    return LEGACY_AGENT_PARAM_PRESET_FILE


def load_agent_param_presets() -> dict[str, Any]:
    return json.loads(resolve_agent_param_preset_file().read_text(encoding="utf-8"))


def select_agent_param_preset(*, iteration_index: int) -> dict[str, Any]:
    payload = load_agent_param_presets()
    presets = payload.get("presets", [])
    if not presets:
        raise ValueError(
            f"agent param preset file `{resolve_agent_param_preset_file()}` contains no presets"
        )

    selected_index = min(max(iteration_index, 0), len(presets) - 1)
    preset = dict(presets[selected_index])
    branch_executions: list[SchemeBranchExecutionSpec] = []
    agents: list[TickAgentParams] = []
    agent_index = 0
    for branch in preset.get("branches", []):
        branch_agents = []
        for item in branch.get("agents", []):
            agent_index += 1
            agent = TickAgentParams.model_validate(item).model_copy(
                update={"agent_instance_id": str(agent_index)}
            )
            branch_agents.append(agent)
            agents.append(agent)
        branch_executions.append(
            SchemeBranchExecutionSpec(
                branch_id=int(branch["branch_id"]),
                planned_agent_params=branch_agents,
            )
        )

    preset["branch_executions"] = branch_executions
    preset["agents"] = agents
    return preset
