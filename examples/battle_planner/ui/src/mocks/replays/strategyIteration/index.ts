import type {
  ReplayRound,
  ReplaySeedRun,
  StrategyIterationReplay,
} from '../../../types/iterationReplay'
import round01 from './rounds/round-01.json'
import round02 from './rounds/round-02.json'
import round03 from './rounds/round-03.json'
import round04 from './rounds/round-04.json'
import round05 from './rounds/round-05.json'
import round06 from './rounds/round-06.json'
import round07 from './rounds/round-07.json'
import round08 from './rounds/round-08.json'
import round09 from './rounds/round-09.json'
import round10 from './rounds/round-10.json'
import round11 from './rounds/round-11.json'
import round12 from './rounds/round-12.json'
import round13 from './rounds/round-13.json'
import round14 from './rounds/round-14.json'
import round15 from './rounds/round-15.json'

type ReplayRoundFixture = Omit<ReplayRound, 'seedRuns'>

const roundFixtures = [
  round01,
  round02,
  round03,
  round04,
  round05,
  round06,
  round07,
  round08,
  round09,
  round10,
  round11,
  round12,
  round13,
  round14,
  round15,
] satisfies ReplayRoundFixture[]

export const strategyIterationRounds = roundFixtures.map((round) => ({
  ...round,
  seedRuns: buildSeedRuns(round),
})) satisfies ReplayRound[]

export const strategyIterationReplay = {
  configuredStrategy: {
    id: 'configured-strategy-east-sea-branch-a',
    name: '东部海域压制 / 分支 A',
    schemeName: '海上关键目标压制验证方案',
    branchName: '空海协同打击分支',
    description: '毁伤优先，消耗受控，低暴露；用于验证多轮策略迭代展示。',
    savedAt: '2026-05-26T10:30:00+08:00',
  },
  selectedSession: {
    sessionId: 'session_0526_A',
    displayName: '15 轮策略迭代展示样例',
    status: 'completed',
    totalRounds: strategyIterationRounds.length,
    seedCount: 8,
    startedAt: '2026-05-26T10:45:00+08:00',
    updatedAt: '2026-05-26T14:20:00+08:00',
    stopReason: '推荐轮次通过稳定性验证',
  },
  implementation: {
    title: '空海协同压制策略实现',
    description:
      '将上游分支策略转成两批次协同打击计划，在每轮仿真中调整进入窗口、火力分配和风险控制，并用多 seed 聚合结果判断是否继续收敛。',
    items: [
      {
        label: '策略来源',
        value: '海上关键目标压制验证方案 / 空海协同打击分支',
      },
      {
        label: '执行目标',
        value: '提高关键目标毁伤，同时控制武器消耗和平台暴露',
      },
      {
        label: '协同方式',
        value: '空对海打击智能体与舰对海打击智能体分批协同',
      },
      {
        label: '执行窗口',
        value: '双批次进入窗口，围绕目标暴露窗口动态调整间隔',
      },
      {
        label: '目标对象',
        value: '红方航母核心目标',
      },
      {
        label: '评估方式',
        value: '每轮 8 局并行仿真，聚合 score、毁伤、消耗、风险和稳定性',
      },
    ],
  },
  recommendedRoundId: 'round-15',
  rounds: strategyIterationRounds,
  dataSupport: [
    {
      label: 'session 状态、轮次、停止原因',
      support: 'direct',
      source: 'session.json',
      note: '真实 artifact 已经包含这些字段。',
    },
    {
      label: 'score、目标毁伤、请求火力、未执行智能体',
      support: 'direct',
      source: 'evaluation.json / session.json',
      note: '当前展示 mock 语义对齐这些真实字段。',
    },
    {
      label: '趋势图、指标箭头、report 摘要、参数 diff、seed 聚合',
      support: 'derived',
      source: 'session iterations / summary.md / plan.md / seed runs',
      note: '可由真实 artifact 转换或聚合得到；当前由展示 fixture 提供。',
    },
    {
      label: '平台暴露、采纳/回退/分叉、结构化变化原因',
      support: 'unsupported',
      source: 'future artifact',
      note: '当前真实 artifact 不直接提供，需要后续补充结构化字段。',
    },
  ],
} satisfies StrategyIterationReplay

function buildSeedRuns(round: ReplayRoundFixture): ReplaySeedRun[] {
  const count = clampInt(round.seedStats.seedCount, 3, 10)
  const successCount = Math.round(count * round.seedStats.successRate)
  const failureReasons = round.seedStats.failureReasons.filter((item) => item.count > 0)

  return Array.from({ length: count }, (_, index) => {
    const isWorst = index === 0
    const isBest = index === count - 1
    const centered = index - (count - 1) / 2
    const score = isWorst
      ? round.seedStats.worstScore
      : isBest
        ? round.seedStats.bestScore
        : round.seedStats.meanScore + centered * round.seedStats.stdScore * 0.28
    const normalizedScore = roundScore(score)
    const success = index >= count - successCount
    const failureReason = success
      ? undefined
      : failureReasons[index % Math.max(failureReasons.length, 1)]?.reason

    return {
      seed: 4100 + round.roundNumber * 10 + index,
      status: success ? 'success' : 'failed',
      score: normalizedScore,
      targetDamageRatio: boundedRatio(
        round.metrics.targetDamageRatio + (normalizedScore - round.seedStats.meanScore) / 240,
      ),
      weaponCostRatio: boundedRatio(
        round.metrics.weaponCostRatio + (index % 3 - 1) * 0.015,
      ),
      platformRiskRatio: boundedRatio(
        round.metrics.platformRiskRatio + (success ? -0.01 : 0.018),
      ),
      success,
      failureReason,
    }
  })
}

function clampInt(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, Math.round(value)))
}

function roundScore(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)))
}

function boundedRatio(value: number) {
  return Number(Math.max(0, Math.min(1, value)).toFixed(2))
}
