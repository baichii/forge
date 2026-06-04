from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forge.core.specs import TickAgentParams

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[1]
DISPLAY_PRESET_FILE = (
    BATTLE_PLANNER_ROOT / "workspace" / "source" / "runtime_presets" / "zc3_lite_agent_params.json"
)
LEGACY_DISPLAY_PRESET_FILE = Path(__file__).with_name("presets") / "zc3_lite_agent_params.json"


def resolve_display_preset_file() -> Path:
    if DISPLAY_PRESET_FILE.exists() or not LEGACY_DISPLAY_PRESET_FILE.exists():
        return DISPLAY_PRESET_FILE
    return LEGACY_DISPLAY_PRESET_FILE


def load_display_agent_param_presets() -> dict[str, Any]:
    return json.loads(resolve_display_preset_file().read_text(encoding="utf-8"))


def select_display_agent_param_preset(*, iteration_index: int) -> dict[str, Any]:
    payload = load_display_agent_param_presets()
    presets = payload.get("presets", [])
    if not presets:
        raise ValueError(f"display preset file `{resolve_display_preset_file()}` contains no presets")

    selected_index = min(max(iteration_index, 0), len(presets) - 1)
    preset = dict(presets[selected_index])
    preset["agents"] = [TickAgentParams.model_validate(item) for item in preset.get("agents", [])]
    return preset
