import type {
  BranchHumanInput,
  PlanHumanInput,
  RunIterationOutput,
  RunOutput,
  TaskContext,
  TaskContextCreateRequest,
  TaskContextListItemView,
  TaskPlan,
  TaskRunCreateRequest,
  TaskRunListItemView,
} from './types'

const createdAt = new Date().toISOString()

export const mockTaskPlans: TaskPlan[] = [
  {
    plan_id: '2175600675558391808',
    name: '海上航母编队打击任务方案',
    scenario_name: 'zc3_lite',
    side: 'blue',
    opponent_side: 'red',
    objective:
      '在控制武器消耗与作战风险的前提下，组织蓝方空中和海上打击力量，对红方航母编队核心舰实施压制和毁伤。',
    constraints: [
      '方案仅使用当前想定已登记的空对海和海对海打击能力，不引入新增能力类型。',
      '打击目标优先级以红方航母为核心，伴随舰艇只作为必要补充目标。',
      '火力配置需要兼顾毁伤效果与武器消耗，避免无依据的集中饱和打击。',
      '红方行动按想定默认策略处理，不在任务方案层预设敌方临机动作。',
    ],
    branches: [
      {
        branch_id: 1,
        name: '空对海打击',
        description:
          '以蓝方空中打击力量为主，对红方航母编队核心目标实施空对海打击，承担主要突击和毁伤压力。',
        platform: {
          summary:
            '上游平台建议将空中打击分支作为主要突击方向，优先匹配具备空对海打击能力的智能体。',
          items: [
            '优先选择能够对海上大型舰艇实施空对海打击的蓝方空中单位。',
            '火力分配以红方航母为主目标，必要时保留对伴随舰艇的扩展空间。',
            '参数生成时重点控制出动批次、武器数量和目标选择，避免混入海基打击逻辑。',
          ],
        },
      },
      {
        branch_id: 2,
        name: '海对海打击',
        description:
          '以蓝方水面舰艇和舰载武器为主，对红方航母编队实施海对海打击，承担补充毁伤和火力平衡任务。',
        platform: {
          summary:
            '上游平台建议将海对海打击分支作为补充打击方向，优先匹配具备舰对海打击能力的智能体。',
          items: [
            '优先选择能够对海上大型舰艇实施舰载武器打击的蓝方水面单位。',
            '火力使用以补足航母毁伤为主，避免与空中打击分支形成重复过量配置。',
            '参数生成时重点控制发射平台、武器数量和目标选择，避免承担空中突击分支职责。',
          ],
        },
      },
    ],
    meta: {},
  },
]

let contextSequence = 1
let runSequence = 1
const mockTaskContexts: TaskContext[] = [buildInitialContext()]
const mockRunOutputs: RunOutput[] = [
  buildRunOutput(
    mockTaskContexts[0],
    'mock-run-001',
    '航母编队打击验证 · 基线运行',
    10,
    3,
  ),
]

export async function listMockPlans(): Promise<TaskPlan[]> {
  return mockTaskPlans.map((plan) => structuredClone(plan))
}

export async function getMockPlan(planId: string): Promise<TaskPlan> {
  const plan = mockTaskPlans.find((item) => item.plan_id === planId)
  if (!plan) {
    throw new Error(`Task plan not found: ${planId}`)
  }
  return structuredClone(plan)
}

export async function createMockContext(
  request: TaskContextCreateRequest,
): Promise<TaskContext> {
  const plan = await getMockPlan(request.plan_id)
  const selectedBranchIds = request.branch_humans.length
    ? request.branch_humans.map((item) => item.branch_id)
    : plan.branches.map((branch) => branch.branch_id)
  const branchHumanById = new Map(
    request.branch_humans.map((item) => [item.branch_id, item.human]),
  )
  const now = new Date().toISOString()
  const context: TaskContext = {
    context_id: `mock-context-${String(contextSequence++).padStart(3, '0')}`,
    plan_id: plan.plan_id,
    name: request.name || plan.name,
    plan_name: plan.name,
    scenario_name: plan.scenario_name,
    side: plan.side,
    opponent_side: plan.opponent_side,
    human: request.plan_human,
    branches: plan.branches
      .filter((branch) => selectedBranchIds.includes(branch.branch_id))
      .map((branch) => ({
        branch_id: branch.branch_id,
        name: branch.name,
        description: branch.description,
        human: branchHumanById.get(branch.branch_id) ?? buildEmptyBranchHuman(),
        meta: branch.meta ?? {},
      })),
    meta: {
      created_at: now,
    },
  }
  mockTaskContexts.unshift(context)
  return structuredClone(context)
}

export async function listMockContexts(): Promise<TaskContextListItemView[]> {
  return mockTaskContexts.map((context) => ({
    context_id: context.context_id,
    name: context.name,
    plan_id: context.plan_id,
    plan_name: context.plan_name,
    scenario_name: context.scenario_name,
    branch_count: context.branches.length,
    created_at: String(context.meta.created_at ?? createdAt),
  }))
}

export async function getMockContext(contextId: string): Promise<TaskContext> {
  const context = mockTaskContexts.find((item) => item.context_id === contextId)
  if (!context) {
    throw new Error(`Task context not found: ${contextId}`)
  }
  return structuredClone(context)
}

export async function createMockRun(request: TaskRunCreateRequest): Promise<RunOutput> {
  const context = mockTaskContexts.find((item) => item.context_id === request.context_id)
  if (!context) {
    throw new Error(`Task context not found: ${request.context_id}`)
  }
  const runId = `mock-run-${String(++runSequence).padStart(3, '0')}`
  const runName = request.run_name || `${context.name} 运行 ${runId}`
  const runOutput = buildRunOutput(
    context,
    runId,
    runName,
    request.options.max_iterations,
    request.options.sim_runs_per_scheme,
  )
  mockRunOutputs.unshift(runOutput)
  return structuredClone(runOutput)
}

export async function listMockRuns(): Promise<TaskRunListItemView[]> {
  return mockRunOutputs.map((run) => ({
    run_id: run.run_id,
    run_name: run.run_name,
    context_id: run.context_id,
    context_name: run.context_name,
    plan_id: run.plan_id,
    plan_name: run.plan_name,
    status: run.status,
    iteration_count: run.iterations.length,
    created_at: String(run.meta.created_at ?? createdAt),
  }))
}

export async function getMockRun(runId: string): Promise<RunOutput> {
  const run = mockRunOutputs.find((item) => item.run_id === runId)
  if (!run) {
    throw new Error(`Task run not found: ${runId}`)
  }
  return structuredClone(run)
}

function buildEmptyBranchHuman(): BranchHumanInput {
  return {
    goal: '',
    risk_style: 'balanced',
    constraints: [],
    risk_points: [],
    notes: '',
  }
}

export function buildEmptyPlanHuman(): PlanHumanInput {
  return {
    goal: '',
    risk_style: 'balanced',
    constraints: [],
    risk_points: [],
    notes: '',
  }
}

function buildInitialContext(): TaskContext {
  const plan = mockTaskPlans[0]
  return {
    context_id: `mock-context-${String(contextSequence++).padStart(3, '0')}`,
    plan_id: plan.plan_id,
    name: `${plan.name} · 总体约束版`,
    plan_name: plan.name,
    scenario_name: plan.scenario_name,
    side: plan.side,
    opponent_side: plan.opponent_side,
    human: {
      goal: plan.objective,
      risk_style: 'balanced',
      constraints: plan.constraints,
      risk_points: [],
      notes: '',
    },
    branches: plan.branches.map((branch) => ({
      branch_id: branch.branch_id,
      name: branch.name,
      description: branch.description,
      human: buildEmptyBranchHuman(),
      meta: branch.meta ?? {},
    })),
    meta: {
      created_at: createdAt,
    },
  }
}

function buildRunOutput(
  context: TaskContext,
  runId: string,
  runName: string,
  maxIterations: number,
  simRunsPerScheme = 1,
): RunOutput {
  const iterationCount = Math.max(1, Math.min(maxIterations || 1, 10))
  const simulationCount = Math.max(1, Math.min(simRunsPerScheme || 1, 5))
  const startedAt = new Date().toISOString()
  const endedAt = new Date(Date.parse(startedAt) + iterationCount * 90_000).toISOString()
  const iterations = Array.from({ length: iterationCount }, (_item, index) =>
    buildIteration(runId, index, iterationCount, simulationCount),
  )
  return {
    run_id: runId,
    run_name: runName,
    context_id: context.context_id,
    context_name: context.name,
    plan_id: context.plan_id,
    plan_name: context.plan_name,
    scenario_name: context.scenario_name,
    objective: context.human.goal,
    max_iterations: maxIterations,
    status: 'completed',
    started_at: startedAt,
    ended_at: endedAt,
    iterations,
    metric_trends: buildMetricTrends(iterations),
    meta: {
      created_at: startedAt,
      source: 'mock',
    },
  }
}

function buildIteration(
  runId: string,
  iterationIndex: number,
  iterationCount: number,
  simulationCount: number,
): RunIterationOutput {
  const labels = [
    '探索',
    '火力调整',
    '平衡优化',
    '目标校准',
    '风险压制',
    '火力收敛',
    '稳定验证',
    '边界复核',
    '候选方案',
    '推荐方案',
  ]
  const tagLabel = labels[iterationIndex] ?? `第 ${iterationIndex + 1} 轮`
  const simulationRuns = buildSimulationRuns(iterationIndex, iterationCount, simulationCount)
  return {
    iteration_index: iterationIndex,
    status: 'completed',
    iteration_tags: [
      {
        key: `mock-${iterationIndex}`,
        label: tagLabel,
        reason: '离线数据按后端输出结构构造，用于界面联调。',
      },
    ],
    overall_summary: {
      label: 'overall',
      title: '总体摘要',
      summary:
        iterationIndex + 1 === iterationCount
          ? '当前运行已完成多轮策略迭代，推荐查看最后一轮方案作为后续联调基准。'
          : '当前轮完成方案生成、仿真执行与结果分析，后续轮次继续调整运行参数。',
    },
    effect_summary: {
      label: 'effect',
      title: '效果摘要',
      summary: `第 ${iterationIndex + 1} 轮完成目标效果检查，仿真记录可用于查看当前方案表现。`,
    },
    report_summary: {
      label: 'report',
      title: '仿真报告摘要',
      summary: `本轮包含 ${simulationRuns.length} 次仿真验证记录。`,
    },
    decision_summary: {
      label: 'decision',
      title: '决策建议',
      summary:
        iterationIndex + 1 === iterationCount
          ? '建议将本轮作为当前运行任务的候选结果。'
          : '建议继续执行下一轮，观察多轮结果是否稳定。',
    },
    scheme: {
      scheme_id: iterationIndex + 1,
      run_id: runId,
      branch_executions: [
        {
          branch_id: 1,
          planned_agent_params: [
            {
              agent_instance_id: `air-strike-alpha-${iterationIndex + 1}`,
              agent_name: 'air_to_sea_strike_agent',
              side: 'blue',
              params: {
                start_time: 0,
                end_time: 70,
                side: 'blue',
                target_ids: ['红方航母核心舰'],
                unit_ids: ['蓝方空中编队一组', '蓝方空中编队二组'],
                wp_num: 2 + Math.min(iterationIndex, 6),
              },
            },
            {
              agent_instance_id: `air-strike-bravo-${iterationIndex + 1}`,
              agent_name: 'air_to_sea_strike_agent',
              side: 'blue',
              params: {
                start_time: 12,
                end_time: 70,
                side: 'blue',
                target_ids: ['红方航母核心舰'],
                unit_ids: ['蓝方空中编队三组', '蓝方空中编队四组'],
                wp_num: 1 + Math.min(iterationIndex, 5),
                clear_targets: true,
              },
            },
          ],
          meta: {},
        },
        {
          branch_id: 2,
          planned_agent_params: [
            {
              agent_instance_id: `sea-strike-alpha-${iterationIndex + 1}`,
              agent_name: 'naval_to_sea_strike_agent',
              side: 'blue',
              params: {
                start_time: 10,
                end_time: 70,
                side: 'blue',
                target_ids: ['红方航母核心舰'],
                unit_ids: ['蓝方水面舰艇一组'],
                wp_num: 1 + Math.floor(iterationIndex / 3),
              },
            },
            {
              agent_instance_id: `sea-strike-bravo-${iterationIndex + 1}`,
              agent_name: 'naval_to_sea_strike_agent',
              side: 'blue',
              params: {
                start_time: 20,
                end_time: 70,
                side: 'blue',
                target_ids: ['红方航母核心舰'],
                unit_ids: ['蓝方水面舰艇二组'],
                wp_num: 1 + Math.floor(iterationIndex / 4),
                clear_targets: false,
              },
            },
          ],
          meta: {},
        },
      ],
      callback_params: [],
    },
    simulation_runs: simulationRuns,
    metric_aggregates: buildMetricAggregates(simulationRuns, iterationIndex, iterationCount),
    meta: {},
  }
}

function buildSimulationRuns(
  iterationIndex: number,
  iterationCount: number,
  simulationCount: number,
): RunIterationOutput['simulation_runs'] {
  const progress = iterationCount > 1 ? iterationIndex / (iterationCount - 1) : 1
  return Array.from({ length: simulationCount }, (_item, simulationIndex) => {
    const variance = (simulationIndex - (simulationCount - 1) / 2) * 0.035
    const targetDamageRatio = clampMetric(0.34 + progress * 0.58 + variance)
    const targetDestroyedCount = targetDamageRatio >= 0.82 ? 1 : 0
    const initialHealth = 1000
    const currentHealth = Math.round(initialHealth * (1 - targetDamageRatio))
    const targetDamageRatioByTarget = {
      红方航母核心舰: Number(targetDamageRatio.toFixed(3)),
    }
    const targetStatisticReport = {
      schema_version: 'callback_eval.v0',
      callback_instance_id: `目标状态统计-${iterationIndex + 1}-${simulationIndex + 1}`,
      callback_name: 'target_statistic',
      metrics: {
        target_count: 1,
        target_destroyed_count: targetDestroyedCount,
        target_damage_ratio: targetDamageRatioByTarget,
      },
      payload: {
        targets: {
          红方航母核心舰: {
            alive: targetDestroyedCount === 0,
            initial: {
              health: initialHealth,
              health_percent: 1,
              ammo_count: 0,
            },
            current: {
              health: currentHealth,
              health_percent: Number((currentHealth / initialHealth).toFixed(3)),
              ammo_count: 0,
            },
            delta: {
              health: currentHealth - initialHealth,
              health_percent: Number((currentHealth / initialHealth - 1).toFixed(3)),
              ammo_count: 0,
            },
          },
        },
      },
    }
    return {
      simulation_index: simulationIndex,
      seed: 20260614 + iterationIndex * 10 + simulationIndex,
      simulation_result: {
        steps: 70 + simulationIndex * 3,
        done: true,
        logs: [
          `重置想定 ${simulationIndex + 1}`,
          `执行仿真 ${70 + simulationIndex * 3} 步`,
        ],
        raw_summary: {
          env: 'pysim',
          max_steps: 70,
          stop_reason: 'env_truncated',
          elapsed_seconds: Number((1.42 + simulationIndex * 0.16).toFixed(2)),
          tick_agents: [
            {
              agent_instance_id: `空中打击组-${iterationIndex + 1}`,
              agent_name: 'air_to_sea_strike_agent',
              side: 'blue',
            },
            {
              agent_instance_id: `水面打击组-${iterationIndex + 1}`,
              agent_name: 'naval_to_sea_strike_agent',
              side: 'blue',
            },
          ],
        },
        metrics: {
          target_count: 1,
          target_damage_ratio: targetDamageRatioByTarget,
          target_destroyed_count: targetDestroyedCount,
        },
      },
      callback_reports: {
        目标状态统计: targetStatisticReport,
      },
      summary: {
        label: 'simulation',
        title: `仿真 ${simulationIndex + 1}`,
        summary: '仿真执行完成，指标以离线联调数据形式提供。',
      },
      meta: {},
    }
  })
}

function buildMetricAggregates(
  simulationRuns: RunIterationOutput['simulation_runs'],
  iterationIndex: number,
  iterationCount: number,
): RunIterationOutput['metric_aggregates'] {
  const definitions = [
    {
      key: 'target_damage_ratio',
      name: '目标毁伤比例',
      description: '每个目标单位的毁伤比例。',
    },
    {
      key: 'target_destroyed_count',
      name: '目标摧毁数量',
      description: '终局态势中已经不存在或判定为不存活的目标数量。',
    },
  ]
  return definitions.map((definition) => {
    const values = simulationRuns
      .map((run) => run.simulation_result?.metrics?.[definition.key])
      .flatMap(metricSamples)
    const fallbackValue =
      definition.key === 'target_destroyed_count'
        ? iterationIndex + 1 === iterationCount
          ? 1
          : 0
        : 0
    return {
      ...definition,
      ...calculateAggregate(values.length ? values : [fallbackValue]),
    }
  })
}

function metricSamples(value: unknown): number[] {
  if (typeof value === 'boolean') {
    return []
  }
  if (typeof value === 'number') {
    return [value]
  }
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return Object.values(value).filter(
      (item): item is number => typeof item === 'number' && typeof item !== 'boolean',
    )
  }
  return []
}

function calculateAggregate(values: number[]) {
  const mean = values.reduce((total, value) => total + value, 0) / values.length
  const min = Math.min(...values)
  const max = Math.max(...values)
  const variance =
    values.reduce((total, value) => total + (value - mean) ** 2, 0) / values.length
  return {
    mean: roundMetric(mean),
    min: roundMetric(min),
    max: roundMetric(max),
    std: roundMetric(Math.sqrt(variance)),
  }
}

function clampMetric(value: number) {
  return Math.max(0, Math.min(1, value))
}

function roundMetric(value: number) {
  return Number(value.toFixed(3))
}

function buildMetricTrends(iterations: RunIterationOutput[]): RunOutput['metric_trends'] {
  const trendMap = new Map<string, RunOutput['metric_trends'][number]>()
  iterations.forEach((iteration) => {
    iteration.metric_aggregates.forEach((aggregate) => {
      if (!trendMap.has(aggregate.key)) {
        trendMap.set(aggregate.key, {
          key: aggregate.key,
          name: aggregate.name,
          description: aggregate.description,
          chart_type: 'line',
          points: [],
        })
      }
      trendMap.get(aggregate.key)?.points.push({
        iteration_index: iteration.iteration_index,
        mean: aggregate.mean,
        min: aggregate.min,
        max: aggregate.max,
        std: aggregate.std,
      })
    })
  })
  return Array.from(trendMap.values())
}
