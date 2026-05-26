import type {
  BusinessPreference,
  SchemeView,
  StrategyBranchView,
} from '../types/strategy'

export const schemeViews: SchemeView[] = [
  {
    schemeId: '10001',
    name: '海上航母对抗验证方案',
    scenarioName: 'zc3_lite',
    side: 'blue',
    opponentSide: 'red',
    objective: '在武器消耗受控的前提下压制并摧毁红方航母编队核心舰。',
    constraints: [
      '首轮验证聚焦一个主策略：空中突击、海对海打击，压制并摧毁对方航母。',
      '优先使用现有空对海和舰对海智能体能力，不扩展新能力类型。',
      '默认红方不主动变化，先生成可进入仿真的执行计划。',
    ],
    humanSummary: '人工希望先验证方案、策略与推演配置的数据链路。',
    humanItems: [
      '当前只保留一个策略分支，不考虑备选方案对比。',
      '只评价该策略是否完成摧毁航母目标。',
    ],
    branches: [
      {
        strategyId: 'strategy-carrier-strike-validation',
        name: '空中突击与海对海打击',
        branchLabel: '分支 A',
        description:
          '蓝方先组织空中突击压制红方航母，再使用海对海打击补充毁伤，目标是击沉对方航母。',
        platformSummary: '上游平台建议采用空中突击和海对海打击协同压制红方航母。',
        platformItems: [
          '空中编队在 120 秒后进入攻击窗口。',
          '舰艇编队在空袭后补充打击同一航母目标。',
          '目标是击沉红方航母。',
        ],
        humanSummary: '人工确认本轮只做单策略验证。',
        humanItems: [
          '不要同时优化对手策略。',
          '武器数量先保守，后续根据仿真反馈调整。',
        ],
        tags: ['毁伤优先', '消耗受控', '低暴露'],
        agentDescriptionIds: [
          'air_to_sea_strike_agent',
          'naval_to_sea_strike_agent',
        ],
      },
    ],
  },
]

export function buildSchemePreference(scheme: SchemeView): BusinessPreference {
  return {
    configuredName: `${scheme.name} · 总体约束版`,
    optimizationTarget: '关键目标毁伤最大化',
    riskFocus: '稳健：避免连续高风险窗口',
    constraintNotes: scheme.constraints.join('\n'),
    timeWindowPreference: '优先保持上游方案给定的主打击窗口',
    branchPreference: '保持当前单策略验证，不扩展额外分支。',
    notes: `${scheme.humanSummary}\n${scheme.humanItems.join('\n')}`,
  }
}

export function buildBranchPreference(branch: StrategyBranchView): BusinessPreference {
  return {
    configuredName: `${branch.name} · 业务偏好版`,
    optimizationTarget: '压制并摧毁红方航母核心舰',
    riskFocus: '均衡：接受短时高收益窗口',
    constraintNotes: branch.humanItems.join('\n'),
    timeWindowPreference: branch.platformItems[0] ?? '沿用上游平台时间窗。',
    branchPreference: '先空中突击压制，再由舰艇编队补充打击。',
    notes:
      '若仿真报告显示毁伤不足，下一轮优先调整批次间隔与武器数量偏好。',
  }
}
