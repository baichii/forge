from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forge.core.specs import TickAgentParams

DISPLAY_PRESET_FILE = Path(__file__).with_name("presets") / "zc3_lite_agent_params.json"


def load_display_agent_param_presets() -> dict[str, Any]:
    return json.loads(DISPLAY_PRESET_FILE.read_text(encoding="utf-8"))


def select_display_agent_param_preset(*, iteration_index: int) -> dict[str, Any]:
    payload = load_display_agent_param_presets()
    presets = payload.get("presets", [])
    if not presets:
        raise ValueError(f"display preset file `{DISPLAY_PRESET_FILE}` contains no presets")

    selected_index = min(max(iteration_index, 0), len(presets) - 1)
    preset = dict(presets[selected_index])
    preset["agents"] = [TickAgentParams.model_validate(item) for item in preset.get("agents", [])]
    return preset
