from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battle_planner.orchestration.session import BattlePlannerSessionView

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_SESSIONS_DIR = REPO_ROOT / "examples" / "battle_planner" / "artifacts" / "sessions"
OUTPUT_FILE = (
    REPO_ROOT
    / "examples"
    / "battle_planner"
    / "ui"
    / "src"
    / "mocks"
    / "generated"
    / "sessionReplays.generated.ts"
)


def main() -> None:
    sessions = [_build_session_view(path) for path in _session_dirs()]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(_render_ts(sessions), encoding="utf-8")
    print(f"exported {len(sessions)} session replay fixture(s) to {OUTPUT_FILE}")


def _session_dirs() -> list[Path]:
    if not ARTIFACT_SESSIONS_DIR.exists():
        return []
    return sorted(
        [path for path in ARTIFACT_SESSIONS_DIR.iterdir() if (path / "session.json").exists()],
        key=lambda path: path.name,
    )


def _build_session_view(session_dir: Path) -> dict[str, Any]:
    session_payload = (session_dir / "session.json").read_text(encoding="utf-8")
    session = BattlePlannerSessionView.model_validate_json(session_payload)
    return {
        "sessionId": session.session_id,
        "status": session.status,
        "currentIteration": session.current_iteration,
        "maxIterations": session.max_iterations,
        "stopReason": session.stop_reason,
        "startedAt": session.started_at,
        "updatedAt": session.updated_at,
        "iterations": [
            _build_iteration_view(session_dir, iteration.model_dump(mode="json"))
            for iteration in session.iterations
        ],
    }


def _build_iteration_view(session_dir: Path, iteration: dict[str, Any]) -> dict[str, Any]:
    index = int(iteration["iteration_index"])
    iteration_dir = session_dir / "iterations" / f"{index:03d}"
    evaluation = _read_json(iteration_dir / "evaluation.json")
    runner_report = _read_json(iteration_dir / "runner_report.json")
    summary_md = _read_text(iteration_dir / "summary.md")
    metrics = _as_dict(evaluation.get("mission_metrics"))
    report_env = _as_dict(runner_report.get("env"))

    return {
        "iterationIndex": index,
        "status": iteration.get("status") or "",
        "agentParamPresetId": iteration.get("agent_param_preset_id"),
        "score": _number_or_none(iteration.get("score")),
        "objectiveAchieved": iteration.get("objective_achieved"),
        "targetInitialHealth": _number_or_none(iteration.get("target_initial_health")),
        "targetCurrentHealth": _number_or_none(iteration.get("target_current_health")),
        "targetHealthDelta": _number_or_none(iteration.get("target_health_delta")),
        "targetDamageRatio": _number_or_none(iteration.get("target_damage_ratio")),
        "targetDestroyedCount": _number_or_none(iteration.get("target_destroyed_count")),
        "requestedWeaponCount": _number_or_none(iteration.get("requested_weapon_count")),
        "inactiveAgentCount": _number_or_none(iteration.get("inactive_agent_count")),
        "advice": _sanitize_text(str(iteration.get("advice") or "")),
        "summaryExcerpt": _summary_excerpt(summary_md or str(iteration.get("summary_excerpt") or "")),
        "keyEvents": [_summarize_event(event) for event in _as_list(iteration.get("key_events"))],
        "simulationReport": {
            "decisionSteps": _number_or_none(metrics.get("sim_decision_steps")),
            "envDone": metrics.get("env_done"),
            "stopReason": _sanitize_text(str(report_env.get("stop_reason") or "")),
            "finalSimTime": _number_or_none(report_env.get("final_sim_time")),
            "elapsedSeconds": _number_or_none(report_env.get("elapsed_seconds")),
            "agentActionCount": _number_or_none(metrics.get("agent_action_count")),
        },
        "error": iteration.get("error"),
    }


def _summarize_event(event: Any) -> dict[str, str]:
    payload = _as_dict(event)
    event_name = str(payload.get("event") or "event")
    if event_name == "target_outcome":
        targets = _as_list(payload.get("targets"))
        achieved = payload.get("objective_achieved")
        return {
            "event": event_name,
            "label": "目标状态",
            "summary": f"目标数量 {len(targets)}，目标达成：{_format_bool(achieved)}。",
        }
    if event_name == "weapon_request":
        requested = payload.get("requested_weapon_count")
        return {
            "event": event_name,
            "label": "火力请求",
            "summary": f"本轮请求火力数：{requested if requested is not None else '未记录'}。",
        }
    if event_name == "score_rule":
        return {
            "event": event_name,
            "label": "评分规则",
            "summary": _sanitize_text(str(payload.get("detail") or "使用目标毁伤与火力消耗综合评分。")),
        }
    return {
        "event": event_name,
        "label": _sanitize_text(event_name),
        "summary": _sanitize_text(str(payload.get("detail") or event_name)),
    }


def _summary_excerpt(text: str, *, max_lines: int = 8, max_chars: int = 900) -> str:
    lines = [_sanitize_text(line) for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])[:max_chars]


def _sanitize_text(text: str) -> str:
    replacements = {
        "# Demo 总结": "# 推演总结",
        "Agent 执行": "智能体执行",
        "air_to_sea_strike_agent": "空对海打击智能体",
        "naval_to_sea_strike_agent": "舰对海打击智能体",
        "runner": "推演过程",
        "target_id": "目标",
        "action_count": "动作次数",
        "executed": "已执行",
        "initial_health": "初始生命值",
        "current_health": "当前生命值",
        "issue": "说明",
        "alive": "存活",
        "health_delta": "生命值变化",
        "health_percent_delta": "生命值比例变化",
        "red_CV16 “辽宁”号001型航空母舰_1": "红方航母目标",
        "display_air_firepower_01": "空对海打击智能体",
        "display_air_firepower_02": "空对海打击智能体",
        "display_naval_firepower_01": "舰对海打击智能体",
        "display_naval_firepower_02": "舰对海打击智能体",
    }
    sanitized = text
    for source, target in replacements.items():
        sanitized = sanitized.replace(source, target)
    sanitized = re.sub(r"\bagent\b", "智能体", sanitized)
    sanitized = re.sub(r"\s*智能体\s*", "智能体", sanitized)
    return re.sub(r"\s+", " ", sanitized).strip() if "\n" not in sanitized else sanitized.strip()


def _format_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    return "未记录"


def _number_or_none(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _as_dict(json.loads(path.read_text(encoding="utf-8")))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _render_ts(sessions: list[dict[str, Any]]) -> str:
    generated_at = datetime.now(UTC).isoformat()
    payload = json.dumps(sessions, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "// Generated from battle_planner artifacts. Do not edit manually.",
            f"// generated_at: {generated_at}",
            "import type { SessionReplayView } from '../../types/session'",
            "",
            f"export const sessionReplays = {payload} satisfies SessionReplayView[]",
            "",
        ]
    )


if __name__ == "__main__":
    main()
