import type {
  DeductionAgentStatus,
  DeductionShowcaseView,
  DeductionStage,
} from '../types/deductionShowcase'

const stages: DeductionStage[] = [
  {
    id: 'plan-ready',
    index: '01',
    title: '策略装订',
    status: '已完成',
    statusTone: 'success',
    time: 'T+000',
    description: '已加载已配置策略、业务约束和推荐执行计划。',
  },
  {
    id: 'first-window',
    index: '02',
    title: '第一批次执行',
    status: '已完成',
    statusTone: 'success',
    time: 'T+112',
    description: '第一批次动作完成，关键目标生命值开始下降。',
  },
  {
    id: 'target-confirm',
    index: '03',
    title: '目标确认',
    status: '进行中',
    statusTone: 'processing',
    time: 'T+184',
    description: '系统确认目标仍处于有效压制窗口，允许第二批次进入。',
  },
  {
    id: 'second-window',
    index: '04',
    title: '第二批次进入',
    status: '待确认',
    statusTone: 'warning',
    time: 'T+226',
    description: '第二批次计划即将触发，重点观察风险和火力余量。',
  },
  {
    id: 'effect-review',
    index: '05',
    title: '效果确认',
    status: '未开始',
    statusTone: 'default',
    time: 'T+300',
    description: '等待仿真报告汇总后生成效果说明。',
  },
] 

const agents: DeductionAgentStatus[] = [
  {
    name: '空对海打击智能体',
    role: '第一批次压制',
    status: '已完成动作',
    summary: '完成第一批次火力投送，保留部分弹药余量。',
  },
  {
    name: '舰对海打击智能体',
    role: '第二批次补充打击',
    status: '等待触发',
    summary: '待目标确认后进入第二批次执行窗口。',
  },
  {
    name: '评估与校准模块',
    role: '效果汇总',
    status: '持续观察',
    summary: '跟踪目标毁伤、平台风险和计划完成度。',
  },
]

export const deductionShowcaseView = {
  sessions: [
    {
      id: 'deduction_0527_A',
      displayName: '空海协同推演回放样例',
      strategy: {
        id: 'configured-strategy-east-sea-branch-a',
        name: '东部海域压制 / 分支 A',
        description: '毁伤优先，消耗受控，低暴露；用于展示策略进入推演后的执行效果。',
        objective:
          '在关键目标暴露窗口内完成两批次协同打击，并持续观察目标毁伤、计划进度和平台风险。',
      },
      rounds: [
        {
          id: 'round-10',
          label: 'Round 10 / 当前最佳',
          version: 'V10 稳健短间隔方案',
          status: '已回放',
          statusTone: 'success',
          effect: {
            title: '当前最佳策略效果总览',
            subtitle: '某次迭代产出的单个策略版本',
            currentTime: 'T+210',
            progress: '62%',
            summary:
              '该轮通过回调第一批次进入时间降低风险，并保持第二批次短间隔补充打击。目标毁伤达到阶段阈值，火力消耗仍在业务偏好范围内。',
          },
          stages: stages.slice(0, 4),
          metrics: [
            {
              label: '关键目标毁伤',
              value: '87%',
              trend: '+6% 较基线',
              tone: 'success',
            },
            {
              label: '计划完成度',
              value: '62%',
              trend: '3 / 5 阶段',
              tone: 'processing',
            },
            {
              label: '武器消耗',
              value: '63%',
              trend: '低于约束上限',
              tone: 'success',
            },
            {
              label: '平台风险',
              value: '中低',
              trend: '短暂接近观察阈值',
              tone: 'warning',
            },
          ],
          events: [
            {
              time: 'T+000',
              title: '加载 V10 稳健短间隔方案',
              detail: '策略进入回放队列，执行窗口和两批次动作已装订。',
              tone: 'processing',
            },
            {
              time: 'T+095',
              title: '第一批次进入执行窗口',
              detail: '空中侧开始压制动作，风险低于观察阈值。',
              tone: 'success',
            },
            {
              time: 'T+164',
              title: '关键目标生命值下降',
              detail: '目标毁伤达到 74%，系统继续保持短间隔节奏。',
              tone: 'success',
            },
            {
              time: 'T+210',
              title: '第二批次完成等待',
              detail: '舰艇侧等待目标确认信号，平台风险处于中低水平。',
              tone: 'warning',
            },
          ],
          agents,
        },
        {
          id: 'round-15',
          label: 'Round 15 / 推荐方案',
          version: 'V15 稳定性验证版',
          status: '回放中',
          statusTone: 'processing',
          effect: {
            title: '推荐策略效果总览',
            subtitle: '某次迭代产出的单个策略版本',
            currentTime: 'T+218',
            progress: '68%',
            summary:
              '当前展示的是推荐轮次策略在推演中的执行效果：第二批次进入窗口已打开，目标毁伤达到阶段阈值，系统继续观察风险峰值和火力余量。',
          },
          stages,
          metrics: [
            {
              label: '关键目标毁伤',
              value: '91%',
              trend: '+12% 较上一阶段',
              tone: 'success',
            },
            {
              label: '计划完成度',
              value: '68%',
              trend: '4 / 5 阶段',
              tone: 'processing',
            },
            {
              label: '武器消耗',
              value: '59%',
              trend: '保留火力余量',
              tone: 'success',
            },
            {
              label: '平台风险',
              value: '低',
              trend: '未触发风险阈值',
              tone: 'success',
            },
          ],
          events: [
            {
              time: 'T+000',
              title: '加载 V15 稳定性验证版',
              detail: '推荐策略进入回放队列，读取上一轮收敛后的执行计划。',
              tone: 'processing',
            },
            {
              time: 'T+084',
              title: '第一批次提前进入窗口',
              detail: '空中侧开始执行压制动作，平台风险保持低位。',
              tone: 'success',
            },
            {
              time: 'T+138',
              title: '风险峰值短暂上升',
              detail: '平台暴露接近观察阈值，系统延后第二批次 14 秒。',
              tone: 'warning',
            },
            {
              time: 'T+172',
              title: '空中编队完成第一批次动作',
              detail: '第一批次执行完成，消耗低于策略偏好上限。',
              tone: 'success',
            },
            {
              time: 'T+196',
              title: '舰对海打击进入等待区',
              detail: '舰艇侧动作已进入预定窗口，等待目标确认信号。',
              tone: 'processing',
            },
            {
              time: 'T+218',
              title: '目标压制窗口保持有效',
              detail: '目标状态满足第二批次进入条件，建议继续执行当前计划。',
              tone: 'success',
            },
          ],
          agents,
        },
      ],
    },
  ],
} satisfies DeductionShowcaseView
