// Generated from battle_planner artifacts. Do not edit manually.
// generated_at: 2026-05-26T12:23:25.697270+00:00
import type { SessionReplayView } from '../../types/session'

export const sessionReplays = [
  {
    "sessionId": "bp-20260525-151125-65ecc973",
    "status": "completed",
    "currentIteration": 2,
    "maxIterations": 2,
    "stopReason": "max_iterations",
    "startedAt": "2026-05-25T15:11:25.173279+00:00",
    "updatedAt": "2026-05-25T15:11:25.559216+00:00",
    "iterations": [
      {
        "iterationIndex": 0,
        "status": "complete",
        "agentParamPresetId": "firepower_01_probe",
        "score": 0.0,
        "objectiveAchieved": false,
        "targetInitialHealth": 5560,
        "targetCurrentHealth": 5560,
        "targetHealthDelta": 0,
        "targetDamageRatio": 0,
        "targetDestroyedCount": 0,
        "requestedWeaponCount": 0,
        "inactiveAgentCount": 2,
        "advice": "未下发任何智能体动作，优先检查时间窗口、目标接地和单位匹配。",
        "summaryExcerpt": "# 推演总结\n真实环境执行 70 个决策步，真实评估分数为 0.0，请求火力数为 0。\n作战目标尚未达成。\n## 目标状态\n- 红方航母目标: 存活=True, 初始生命值=5560, 当前生命值=5560, 生命值变化=0, 生命值比例变化=0\n##智能体执行\n- 空对海打击智能体(空对海打击智能体): 动作次数=0, 已执行=False, 说明=未执行动作，需检查时间窗口、目标消失、重复打击或单位/目标匹配。\n- 舰对海打击智能体(舰对海打击智能体): 动作次数=0, 已执行=False, 说明=未执行动作，需检查时间窗口、目标消失、重复打击或单位/目标匹配。",
        "keyEvents": [
          {
            "event": "target_outcome",
            "label": "目标状态",
            "summary": "目标数量 1，目标达成：否。"
          },
          {
            "event": "weapon_request",
            "label": "火力请求",
            "summary": "本轮请求火力数：0。"
          },
          {
            "event": "score_rule",
            "label": "评分规则",
            "summary": "目标摧毁优先；未摧毁时按毁伤比例计分；目标摧毁后对请求火力数做轻量扣分。"
          }
        ],
        "simulationReport": {
          "decisionSteps": 70,
          "envDone": false,
          "stopReason": "max_step",
          "finalSimTime": 70.0,
          "elapsedSeconds": 0.17375898361206055,
          "agentActionCount": 0
        },
        "error": null
      },
      {
        "iterationIndex": 1,
        "status": "complete",
        "agentParamPresetId": "firepower_02_light",
        "score": 0.0,
        "objectiveAchieved": false,
        "targetInitialHealth": 5560,
        "targetCurrentHealth": 5560,
        "targetHealthDelta": 0,
        "targetDamageRatio": 0,
        "targetDestroyedCount": 0,
        "requestedWeaponCount": 0,
        "inactiveAgentCount": 2,
        "advice": "未下发任何智能体动作，优先检查时间窗口、目标接地和单位匹配。",
        "summaryExcerpt": "# 推演总结\n真实环境执行 70 个决策步，真实评估分数为 0.0，请求火力数为 0。\n作战目标尚未达成。\n## 目标状态\n- 红方航母目标: 存活=True, 初始生命值=5560, 当前生命值=5560, 生命值变化=0, 生命值比例变化=0\n##智能体执行\n- 空对海打击智能体(空对海打击智能体): 动作次数=0, 已执行=False, 说明=未执行动作，需检查时间窗口、目标消失、重复打击或单位/目标匹配。\n- 舰对海打击智能体(舰对海打击智能体): 动作次数=0, 已执行=False, 说明=未执行动作，需检查时间窗口、目标消失、重复打击或单位/目标匹配。",
        "keyEvents": [
          {
            "event": "target_outcome",
            "label": "目标状态",
            "summary": "目标数量 1，目标达成：否。"
          },
          {
            "event": "weapon_request",
            "label": "火力请求",
            "summary": "本轮请求火力数：0。"
          },
          {
            "event": "score_rule",
            "label": "评分规则",
            "summary": "目标摧毁优先；未摧毁时按毁伤比例计分；目标摧毁后对请求火力数做轻量扣分。"
          }
        ],
        "simulationReport": {
          "decisionSteps": 70,
          "envDone": false,
          "stopReason": "max_step",
          "finalSimTime": 70.0,
          "elapsedSeconds": 0.16708683967590332,
          "agentActionCount": 0
        },
        "error": null
      }
    ]
  }
] satisfies SessionReplayView[]
