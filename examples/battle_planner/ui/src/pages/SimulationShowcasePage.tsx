import {
  CheckCircleFilled,
  DashboardOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  LineChartOutlined,
  PlayCircleOutlined,
  SlidersOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App as AntdApp,
  Button,
  Card,
  Empty,
  Form,
  Input,
  InputNumber,
  Segmented,
  Select,
  Space,
  Spin,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import type { ECharts, EChartsCoreOption } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { battlePlannerClient } from '../api/battlePlannerClient'
import type {
  RunIterationOutput,
  RunMetricAggregate,
  RunMetricTrend,
  RunOutput,
  RunSimulationRecord,
  SchemeBranchExecution,
  TaskContext,
  TaskContextListItemView,
  TaskRunListItemView,
  TickAgentRunParams,
} from '../api/types'
import './SimulationShowcasePage.css'

const { Paragraph, Text, Title } = Typography

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

type IterationMode = 'create' | 'history'

type RunFormValues = {
  runName: string
  maxIterations: number
  simRunsPerScheme: number
}

type SimulationMetricValue =
  | number
  | string
  | boolean
  | Record<string, unknown>
  | null
  | undefined

const defaultRunOptions: RunFormValues = {
  runName: '',
  maxIterations: 10,
  simRunsPerScheme: 3,
}

const branchNameMap: Record<number, string> = {
  1: '空对海打击分支',
  2: '海对海打击分支',
}

const agentNameMap: Record<string, string> = {
  air_to_sea_strike_agent: '空对海打击智能体',
  naval_to_sea_strike_agent: '海对海打击智能体',
  sea_to_sea_strike_agent: '海对海打击智能体',
}

const paramNameMap: Record<string, string> = {
  clear_targets: '清理目标',
  end_time: '结束时间',
  side: '参演方',
  start_time: '开始时间',
  target_ids: '目标单位',
  unit_ids: '执行单位',
  wp_num: '武器数量',
}

const metricNameMap: Record<string, string> = {
  target_count: '目标数量',
  target_damage_ratio: '目标毁伤比例',
  target_destroyed_count: '目标摧毁数量',
}

const sideNameMap: Record<string, string> = {
  blue: '蓝方',
  red: '红方',
}

const callbackNameMap: Record<string, string> = {
  target_statistic: '目标状态统计',
}

function SimulationShowcasePage() {
  const { message } = AntdApp.useApp()
  const [mode, setMode] = useState<IterationMode>('create')
  const [contexts, setContexts] = useState<TaskContextListItemView[]>([])
  const [runs, setRuns] = useState<TaskRunListItemView[]>([])
  const [selectedContextId, setSelectedContextId] = useState('')
  const [selectedRunId, setSelectedRunId] = useState('')
  const [runOutput, setRunOutput] = useState<RunOutput | null>(null)
  const [runContext, setRunContext] = useState<TaskContext | null>(null)
  const [selectedIterationIndex, setSelectedIterationIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let mounted = true
    Promise.all([
      battlePlannerClient.listContexts(),
      battlePlannerClient.listRuns(),
    ])
      .then(async ([contextItems, runItems]) => {
        if (!mounted) {
          return
        }
        setContexts(contextItems)
        setRuns(runItems)
        setSelectedContextId(contextItems[0]?.context_id ?? '')
        const firstRun = runItems[0]
        if (firstRun) {
          const output = await loadRunWithContext(firstRun.run_id)
          if (!mounted) {
            return
          }
          setSelectedRunId(firstRun.run_id)
          setRunOutput(output.run)
          setRunContext(output.context)
          setSelectedIterationIndex(output.run.iterations.at(-1)?.iteration_index ?? 0)
        }
      })
      .catch((error: unknown) => {
        if (!mounted) {
          return
        }
        setLoadError(error instanceof Error ? error.message : '策略迭代数据读取失败')
      })
      .finally(() => {
        if (mounted) {
          setIsLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  const selectedContext = contexts.find((item) => item.context_id === selectedContextId)
  const selectedIteration = useMemo(
    () =>
      runOutput?.iterations.find((item) => item.iteration_index === selectedIterationIndex) ??
      runOutput?.iterations.at(-1),
    [runOutput, selectedIterationIndex],
  )

  async function handleHistoryRunChange(runId: string) {
    setSelectedRunId(runId)
    const output = await loadRunWithContext(runId)
    setRunOutput(output.run)
    setRunContext(output.context)
    setSelectedIterationIndex(output.run.iterations.at(-1)?.iteration_index ?? 0)
  }

  async function handleCreateRun(values: RunFormValues) {
    if (!selectedContextId) {
      message.warning('请先选择任务上下文')
      return
    }
    setIsCreating(true)
    try {
      const output = await battlePlannerClient.createRun({
        context_id: selectedContextId,
        run_name: values.runName,
        options: {
          workflow_name: 'zc_lite_baseline',
          max_iterations: values.maxIterations,
          sim_runs_per_scheme: values.simRunsPerScheme,
          max_retry: 1,
          timeout_seconds: null,
          extra: {},
        },
      })
      const context = await battlePlannerClient
        .getContext(output.context_id)
        .catch(() => null)
      const nextRuns = await battlePlannerClient.listRuns()
      setRuns(nextRuns)
      setSelectedRunId(output.run_id)
      setRunOutput(output)
      setRunContext(context)
      setSelectedIterationIndex(output.iterations.at(-1)?.iteration_index ?? 0)
      setMode('history')
      message.success('运行任务已创建')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '运行任务创建失败')
    } finally {
      setIsCreating(false)
    }
  }

  if (isLoading) {
    return (
      <main className="showcase-page">
        <Spin description="读取策略迭代数据" />
      </main>
    )
  }

  if (loadError) {
    return (
      <main className="showcase-page">
        <Alert message="策略迭代数据不可用" description={loadError} type="warning" showIcon />
      </main>
    )
  }

  return (
    <main className="showcase-page">
      <section className="showcase-head" aria-labelledby="showcase-title">
        <div>
          <Tag className="showcase-eyebrow">策略迭代</Tag>
          <Title id="showcase-title" level={1}>
            让每轮策略优化都有据可循。
          </Title>
          <Paragraph className="showcase-lead">
            基于已保存的任务上下文创建运行任务，或查看历史运行任务的迭代结果。
          </Paragraph>
        </div>
        <span className="showcase-head__tag">
          {runOutput ? `${runOutput.iterations.length} 轮迭代记录` : '等待选择任务'}
        </span>
      </section>

      <section className="showcase-layout" aria-label="策略迭代工作区">
        <Card className="showcase-panel" variant="borderless">
          <div className="showcase-panel__head">
            <div>
              <Text strong>运行任务</Text>
              <Text>新建运行任务或查看历史推演</Text>
            </div>
            <DashboardOutlined />
          </div>

          <Segmented
            block
            className="showcase-mode"
            value={mode}
            onChange={(value) => setMode(value as IterationMode)}
            options={[
              { label: '新建运行', value: 'create' },
              { label: '查看历史推演', value: 'history' },
            ]}
          />

          {mode === 'create' ? (
            <Form<RunFormValues>
              className="showcase-form"
              initialValues={defaultRunOptions}
              layout="vertical"
              onFinish={handleCreateRun}
            >
              <Form.Item label="任务上下文" required>
                <Select
                  value={selectedContextId || undefined}
                  onChange={setSelectedContextId}
                  options={contexts.map((context) => ({
                    value: context.context_id,
                    label: context.name,
                  }))}
                  placeholder="选择已保存的任务上下文"
                />
              </Form.Item>
              <Form.Item label="运行名称" name="runName">
                <Input placeholder={selectedContext ? `${selectedContext.name} 运行` : '为本次运行命名'} />
              </Form.Item>
              <Form.Item label="最大迭代轮数" name="maxIterations">
                <InputNumber className="showcase-full-input" min={1} max={10} />
              </Form.Item>
              <Form.Item label="每轮仿真次数" name="simRunsPerScheme">
                <InputNumber className="showcase-full-input" min={1} max={3} />
              </Form.Item>
              <Button
                block
                htmlType="submit"
                icon={<PlayCircleOutlined />}
                loading={isCreating}
                type="primary"
              >
                创建并运行
              </Button>
            </Form>
          ) : (
            <div className="showcase-history-panel">
              <div className="showcase-field">
                <Text strong>历史推演任务</Text>
                <Select
                  value={selectedRunId || undefined}
                  onChange={handleHistoryRunChange}
                  options={runs.map((run) => ({
                    value: run.run_id,
                    label: run.run_name,
                  }))}
                  placeholder="选择历史运行任务"
                />
              </div>
            </div>
          )}

          {runOutput ? (
            <>
              <div className="showcase-session-card">
                <strong>{runOutput.run_name}</strong>
                <span>{runOutput.context_name}</span>
                <span>
                  {runOutput.plan_name} · {runOutput.iterations.length} 轮 · {runOutput.scenario_name}
                </span>
              </div>

              <div className="showcase-round-list" aria-label="策略轮次列表">
                {runOutput.iterations.map((iteration) => (
                  <button
                    className={
                      iteration.iteration_index === selectedIteration?.iteration_index
                        ? 'showcase-round-button showcase-round-button--active'
                        : 'showcase-round-button'
                    }
                    key={iteration.iteration_index}
                    type="button"
                    onClick={() => setSelectedIterationIndex(iteration.iteration_index)}
                  >
                    <span>第 {iteration.iteration_index + 1} 轮</span>
                    <strong>{iterationTitle(iteration)}</strong>
                    <em>{statusText(iteration.status)}</em>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <Empty className="showcase-empty" description="暂无运行任务" />
          )}
        </Card>

        <Card className="showcase-detail" variant="borderless">
          {runOutput && selectedIteration ? (
            <RunDetail
              runContext={runContext}
              runOutput={runOutput}
              selectedIteration={selectedIteration}
            />
          ) : (
            <Empty className="showcase-empty" description="请选择或创建运行任务" />
          )}
        </Card>
      </section>
    </main>
  )
}

async function loadRunWithContext(runId: string) {
  const run = await battlePlannerClient.getRun(runId)
  const context = await battlePlannerClient.getContext(run.context_id).catch(() => null)
  return { context, run }
}

function RunDetail({
  runContext,
  runOutput,
  selectedIteration,
}: {
  runContext: TaskContext | null
  runOutput: RunOutput
  selectedIteration: RunIterationOutput
}) {
  const previousIteration = getPreviousIteration(runOutput, selectedIteration)
  return (
    <>
      <RunOverviewCard
        runContext={runContext}
        runOutput={runOutput}
        selectedIteration={selectedIteration}
      />
      <MetricAggregatePanel
        runOutput={runOutput}
        selectedIteration={selectedIteration}
      />

      <div className="showcase-round-detail">
        <div className="showcase-round-head">
          <div>
            <Text>当前轮次</Text>
            <Title level={3}>
              第 {selectedIteration.iteration_index + 1} 轮 / {iterationTitle(selectedIteration)}
            </Title>
            <Paragraph>{selectedIteration.overall_summary?.summary || '暂无本轮总体摘要。'}</Paragraph>
          </div>
          <Tag>{statusText(selectedIteration.status)}</Tag>
        </div>

        <RoundMetricPanel
          previousIteration={previousIteration}
          selectedIteration={selectedIteration}
        />

        <div className="showcase-detail-grid">
          <SummaryArticle
            icon={<FileTextOutlined />}
            title="效果摘要"
            text={selectedIteration.effect_summary?.summary}
          />
          <SummaryArticle
            icon={<ExperimentOutlined />}
            title="仿真报告摘要"
            text={selectedIteration.report_summary?.summary}
          />
          <SummaryArticle
            title="决策建议"
            text={selectedIteration.decision_summary?.summary}
          />
          <article>
            <Text strong>轮次标签</Text>
            <div className="showcase-diff-list">
              {selectedIteration.iteration_tags.length ? (
                selectedIteration.iteration_tags.map((tag) => (
                  <span key={`${tag.key}-${tag.label}`}>
                    <CheckCircleFilled /> {tag.label}：{tag.reason}
                  </span>
                ))
              ) : (
                <span>暂无标签</span>
              )}
            </div>
          </article>
        </div>

        <Tabs
          className="showcase-secondary-tabs"
          items={[
            {
              key: 'simulation',
              label: '仿真记录',
              children: <SimulationPanel selectedIteration={selectedIteration} />,
            },
            {
              key: 'scheme',
              label: '运行参数',
              children: <SchemePanel selectedIteration={selectedIteration} />,
            },
          ]}
        />
      </div>
    </>
  )
}

function RoundMetricPanel({
  previousIteration,
  selectedIteration,
}: {
  previousIteration?: RunIterationOutput
  selectedIteration: RunIterationOutput
}) {
  const previousByKey = new Map(
    (previousIteration?.metric_aggregates ?? []).map((aggregate) => [
      aggregate.key,
      aggregate,
    ]),
  )
  return (
    <div className="showcase-metrics showcase-metrics--round">
      {selectedIteration.metric_aggregates.length ? (
        selectedIteration.metric_aggregates.map((aggregate) => {
          const change = metricMeanChange(aggregate, previousByKey.get(aggregate.key))
          return (
            <div key={aggregate.key}>
              <Text>{aggregate.name}</Text>
              <strong>{formatMetricValue(aggregate.mean, aggregate)}</strong>
              <small className={`showcase-delta ${change.className}`}>
                {change.text}
              </small>
            </div>
          )
        })
      ) : (
        <div>
          <Text>指标</Text>
          <strong>暂无</strong>
          <small>本轮没有聚合指标</small>
        </div>
      )}
    </div>
  )
}

function RunOverviewCard({
  runContext,
  runOutput,
  selectedIteration,
}: {
  runContext: TaskContext | null
  runOutput: RunOutput
  selectedIteration: RunIterationOutput
}) {
  const [now, setNow] = useState(() => Date.now())
  const constraints = runContext?.human.constraints ?? []

  useEffect(() => {
    if (runOutput.status !== 'running') {
      return undefined
    }
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [runOutput.status])

  return (
    <section className="showcase-session-brief" aria-label="运行总览">
      <div className="showcase-session-brief__head">
        <div>
          <Tag className="showcase-eyebrow">运行总览</Tag>
          <Title level={2}>{runOutput.run_name}</Title>
          <Paragraph>
            {statusText(runOutput.status)} ·{' '}
            {runOutput.status === 'running' ? '运行时间' : '总耗时'}{' '}
            {formatDuration(runOutput.started_at, runOutput.ended_at, now)}
          </Paragraph>
        </div>
        <Tag color={statusColor(runOutput.status)}>{statusText(runOutput.status)}</Tag>
      </div>

      <div className="showcase-overview-groups">
        <div className="showcase-overview-grid showcase-overview-grid--triple">
          <Info label="任务方案" value={runOutput.plan_name} />
          <Info label="任务上下文" value={runOutput.context_name} />
          <Info label="想定" value={runOutput.scenario_name || '-'} />
        </div>
        <div className="showcase-overview-grid showcase-overview-grid--triple">
          <Info label="己方" value={formatSideName(runContext?.side ?? '')} />
          <Info label="敌方" value={formatSideName(runContext?.opponent_side ?? '')} />
          <Info label="分支数" value={String(runContext?.branches.length ?? '-')} />
        </div>
        <div className="showcase-overview-grid showcase-overview-grid--double">
          <Info
            label="迭代进度"
            value={`${runOutput.iterations.length} / ${runOutput.max_iterations ?? '-'}`}
          />
          <Info
            label="当前轮次标签"
            value={`第 ${selectedIteration.iteration_index + 1} 轮 · ${iterationTitle(selectedIteration)}`}
          />
        </div>
      </div>

      <div className="showcase-overview-texts">
        <article>
          <Text strong>作战目标</Text>
          <Paragraph>{runOutput.objective || '暂无任务目标。'}</Paragraph>
        </article>
        <article aria-label="总体约束">
          <Text strong>总体约束</Text>
          <div className="showcase-constraint-list">
            {constraints.length ? (
              constraints.map((constraint) => (
                <span key={constraint}>{constraint}</span>
              ))
            ) : (
              <span>暂无约束</span>
            )}
          </div>
        </article>
      </div>
    </section>
  )
}

function MetricAggregatePanel({
  runOutput,
  selectedIteration,
}: {
  runOutput: RunOutput
  selectedIteration: RunIterationOutput
}) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<ECharts | null>(null)
  const metricOptions = useMemo(
    () =>
      runOutput.metric_trends.map((trend) => ({
        label: trend.name,
        value: trend.key,
      })),
    [runOutput.metric_trends],
  )
  const [selectedMetricKey, setSelectedMetricKey] = useState(metricOptions[0]?.value ?? '')
  const activeMetricKey = metricOptions.some((option) => option.value === selectedMetricKey)
    ? selectedMetricKey
    : metricOptions[0]?.value ?? ''
  const selectedTrend = runOutput.metric_trends.find((trend) => trend.key === activeMetricKey)
  const selectedAggregate = selectedIteration.metric_aggregates.find(
    (aggregate) => aggregate.key === activeMetricKey,
  )

  useEffect(() => {
    const chartElement = chartRef.current
    if (!chartElement || !selectedTrend) {
      return undefined
    }
    const chart =
      echarts.getInstanceByDom(chartElement) ??
      echarts.init(chartElement, undefined, { renderer: 'canvas' })
    chartInstanceRef.current = chart
    chart.setOption(
      buildMetricTrendOption(selectedTrend, selectedIteration.iteration_index),
      { notMerge: true },
    )
    let resizeFrame = 0
    const resizeObserver = new ResizeObserver(() => {
      window.cancelAnimationFrame(resizeFrame)
      resizeFrame = window.requestAnimationFrame(() => chart.resize())
    })
    resizeObserver.observe(chartElement)
    return () => {
      window.cancelAnimationFrame(resizeFrame)
      resizeObserver.disconnect()
    }
  }, [selectedIteration.iteration_index, selectedTrend])

  useEffect(
    () => () => {
      chartInstanceRef.current?.dispose()
      chartInstanceRef.current = null
    },
    [],
  )

  return (
    <section className="showcase-aggregate-panel" aria-label="聚合指标">
      <div className="showcase-section-title">
        <span>
          <LineChartOutlined /> 多局指标展示
        </span>
        <Select
          className="showcase-metric-select"
          options={metricOptions}
          placeholder="选择指标"
          value={activeMetricKey || undefined}
          onChange={setSelectedMetricKey}
        />
      </div>
      {selectedTrend && selectedAggregate ? (
        <>
          <div className="showcase-trend-strip" aria-label="当前轮指标统计">
            <span>
              当前轮 <strong>第 {selectedIteration.iteration_index + 1} 轮</strong>
            </span>
            <span>
              均值 <strong>{formatMetricValue(selectedAggregate.mean, selectedAggregate)}</strong>
            </span>
            <span>
              方差 <strong>{formatVarianceValue(metricVariance(selectedAggregate))}</strong>
            </span>
            <span>
              标准差 <strong>{formatMetricValue(selectedAggregate.std, selectedAggregate)}</strong>
            </span>
          </div>
          <div
            ref={chartRef}
            className="showcase-line-chart showcase-line-chart--metric"
            role="img"
            aria-label={`${selectedTrend.name} 均值折线图`}
          />
        </>
      ) : (
        <div className="showcase-empty-inline">暂无聚合指标</div>
      )}
    </section>
  )
}

function SummaryArticle({
  icon,
  title,
  text,
}: {
  icon?: ReactNode
  title: string
  text?: string
}) {
  return (
    <article>
      <Space>
        {icon}
        <Text strong>{title}</Text>
      </Space>
      <Paragraph>{text || '暂无内容'}</Paragraph>
    </article>
  )
}

function SimulationPanel({ selectedIteration }: { selectedIteration: RunIterationOutput }) {
  const aggregateByKey = new Map(
    selectedIteration.metric_aggregates.map((aggregate) => [aggregate.key, aggregate]),
  )
  return (
    <div className="showcase-seed-panel">
      <div className="showcase-section-title">
        <span>
          <ExperimentOutlined /> 本轮多局仿真指标明细
        </span>
        <Text>{selectedIteration.simulation_runs.length} 条记录</Text>
      </div>

      <div className="showcase-sim-aggregate-grid" aria-label="本轮多局指标概览">
        {selectedIteration.metric_aggregates.length ? (
          selectedIteration.metric_aggregates.map((aggregate) => (
            <article key={aggregate.key}>
              <Text>{aggregate.name}</Text>
              <strong>{formatMetricValue(aggregate.mean, aggregate)}</strong>
              <div>
                <span>最小 {formatMetricValue(aggregate.min, aggregate)}</span>
                <span>最大 {formatMetricValue(aggregate.max, aggregate)}</span>
                <span>标准差 {formatMetricValue(aggregate.std, aggregate)}</span>
              </div>
            </article>
          ))
        ) : (
          <div className="showcase-empty-inline">本轮暂无聚合指标</div>
        )}
      </div>

      <div className="showcase-sim-matrix" aria-label="单局指标矩阵">
        <div className="showcase-sim-matrix__row showcase-sim-matrix__row--head">
          <span>仿真局次</span>
          {selectedIteration.metric_aggregates.map((aggregate) => (
            <span key={aggregate.key}>{aggregate.name}</span>
          ))}
          <span>步数</span>
          <span>结束状态</span>
        </div>
        {selectedIteration.simulation_runs.map((run) => (
          <div className="showcase-sim-matrix__row" key={run.simulation_index}>
            <span>
              <strong>仿真 {run.simulation_index + 1}</strong>
              <em>种子 {run.seed ?? '-'}</em>
            </span>
            {selectedIteration.metric_aggregates.map((aggregate) => (
              <span key={aggregate.key}>
                {formatSimulationMetricValue(
                  run.simulation_result?.metrics?.[aggregate.key],
                  aggregate,
                )}
              </span>
            ))}
            <span>{run.simulation_result?.steps ?? '-'}</span>
            <span>{run.simulation_result?.done ? '已结束' : '未结束'}</span>
          </div>
        ))}
      </div>

      <div className="showcase-sim-detail-list" aria-label="单局仿真详情">
        {selectedIteration.simulation_runs.map((run) => (
          <SimulationRunDetailCard
            aggregateByKey={aggregateByKey}
            key={run.simulation_index}
            run={run}
          />
        ))}
      </div>
    </div>
  )
}

function SimulationRunDetailCard({
  aggregateByKey,
  run,
}: {
  aggregateByKey: Map<string, RunMetricAggregate>
  run: RunSimulationRecord
}) {
  const rawSummary = asRecord(run.simulation_result?.raw_summary)
  const tickAgents = Array.isArray(rawSummary.tick_agents) ? rawSummary.tick_agents : []
  const stopReason = typeof rawSummary.stop_reason === 'string' ? rawSummary.stop_reason : ''
  const elapsedSeconds =
    typeof rawSummary.elapsed_seconds === 'number' ? rawSummary.elapsed_seconds : undefined
  const rawMetrics = Object.entries(run.simulation_result?.metrics ?? {}).filter(
    ([, value]) => typeof value !== 'number' && !isNumericRecord(value),
  )

  return (
    <details className="showcase-sim-detail-card">
      <summary>
        <span>
          <strong>仿真 {run.simulation_index + 1}</strong>
          <em>{run.summary?.summary ?? '暂无摘要'}</em>
        </span>
        <span>{run.seed ? `种子 ${run.seed}` : '无随机种子'}</span>
      </summary>

      <div className="showcase-sim-runtime-grid">
        <Info label="执行步数" value={String(run.simulation_result?.steps ?? '-')} />
        <Info label="结束状态" value={run.simulation_result?.done ? '已结束' : '未结束'} />
        <Info label="停止原因" value={formatStopReason(stopReason)} />
        <Info label="运行耗时" value={formatElapsedSeconds(elapsedSeconds)} />
        <Info label="参与智能体" value={`${tickAgents.length} 个`} />
      </div>

      <div className="showcase-sim-detail-section">
        <Text strong>单局指标</Text>
        <div className="showcase-sim-raw-metrics">
          {Object.entries(run.simulation_result?.metrics ?? {}).length ? (
            Object.entries(run.simulation_result?.metrics ?? {}).map(([key, value]) => (
              <span key={key}>
                <Text>{formatMetricName(key, aggregateByKey)}</Text>
                <strong>{formatSimulationMetricValue(value, aggregateByKey.get(key))}</strong>
              </span>
            ))
          ) : (
            <span>暂无指标</span>
          )}
        </div>
      </div>

      {rawMetrics.length ? (
        <div className="showcase-sim-detail-section">
          <Text strong>补充信息</Text>
          <div className="showcase-sim-raw-metrics">
            {rawMetrics.map(([key, value]) => (
              <span key={key}>
                <Text>{formatMetricName(key, aggregateByKey)}</Text>
                <strong>{formatParamValue(value)}</strong>
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <CallbackReportDetails callbackReports={run.callback_reports ?? {}} />
    </details>
  )
}

function CallbackReportDetails({
  callbackReports,
}: {
  callbackReports: Record<string, unknown>
}) {
  const reports = Object.entries(callbackReports)
  if (!reports.length) {
    return (
      <div className="showcase-sim-detail-section">
        <Text strong>Callback 报告</Text>
        <p>暂无 callback 报告。</p>
      </div>
    )
  }

  return (
    <div className="showcase-sim-detail-section">
      <Text strong>Callback 报告</Text>
      <div className="showcase-callback-list">
        {reports.map(([reportKey, reportValue]) => {
          const report = asRecord(reportValue)
          const callbackName = String(report.callback_name ?? reportKey)
          return callbackName === 'target_statistic' ? (
            <TargetStatisticReportCard
              key={reportKey}
              report={report}
              reportKey={reportKey}
            />
          ) : (
            <article key={reportKey}>
              <strong>{formatCallbackName(callbackName)}</strong>
              <span>
                指标 {Object.keys(asRecord(report.metrics)).length} 项 · 明细{' '}
                {Object.keys(asRecord(report.payload)).length} 项
              </span>
            </article>
          )
        })}
      </div>
    </div>
  )
}

function TargetStatisticReportCard({
  report,
  reportKey,
}: {
  report: Record<string, unknown>
  reportKey: string
}) {
  const payload = asRecord(report.payload)
  const targets = asRecord(payload.targets)
  return (
    <article className="showcase-target-report">
      <div className="showcase-target-report__head">
        <strong>{formatCallbackName(String(report.callback_name ?? reportKey))}</strong>
        <span>{Object.keys(targets).length} 个目标</span>
      </div>
      <div className="showcase-target-list">
        {Object.entries(targets).length ? (
          Object.entries(targets).map(([targetId, targetValue]) => {
            const target = asRecord(targetValue)
            const initial = asRecord(target.initial)
            const current = asRecord(target.current)
            const delta = asRecord(target.delta)
            return (
              <div key={targetId}>
                <strong>{targetId}</strong>
                <Tag color={target.alive === false ? 'error' : 'success'}>
                  {target.alive === false ? '已摧毁' : '存活'}
                </Tag>
                <span>初始生命 {formatUnknownMetricValue(initial.health)}</span>
                <span>当前生命 {formatUnknownMetricValue(current.health)}</span>
                <span>生命变化 {formatUnknownMetricValue(delta.health)}</span>
                <span>
                  毁伤比例{' '}
                  {formatDamageRatioFromTarget(initial.health, delta.health)}
                </span>
              </div>
            )
          })
        ) : (
          <span>暂无目标明细</span>
        )}
      </div>
    </article>
  )
}

function SchemePanel({ selectedIteration }: { selectedIteration: RunIterationOutput }) {
  const branchExecutions = selectedIteration.scheme?.branch_executions ?? []
  return (
    <div className="showcase-execution">
      <div className="showcase-section-title">
        <span>
          <SlidersOutlined /> 当前轮运行参数
        </span>
        <Text>按分支查看智能体输入参数</Text>
      </div>
      <div className="showcase-agent-branches" aria-label="分支智能体运行参数">
        {branchExecutions.length ? (
          branchExecutions.map((branch) => (
            <BranchAgentParamsCard
              branch={branch}
              key={branch.branch_id ?? 'unknown'}
            />
          ))
        ) : (
          <div className="showcase-agent-empty">暂无分支执行参数</div>
        )}
      </div>
    </div>
  )
}

function BranchAgentParamsCard({ branch }: { branch: SchemeBranchExecution }) {
  const agents = branch.planned_agent_params ?? []
  const [selectedAgentIndex, setSelectedAgentIndex] = useState('0')
  const activeIndex = agents[Number(selectedAgentIndex)] ? Number(selectedAgentIndex) : 0
  const activeAgent = agents[activeIndex]

  return (
    <article className="showcase-agent-branch">
      <div className="showcase-agent-branch__head">
        <Text strong>{formatBranchName(branch.branch_id)}</Text>
        <span>{agents.length} 个智能体</span>
      </div>
      {agents.length ? (
        <>
          <Segmented
            block
            className="showcase-agent-switch"
            options={agents.map((agent, index) => ({
              label: `${formatAgentName(agent.agent_name)} ${index + 1}`,
              value: String(index),
            }))}
            value={String(activeIndex)}
            onChange={(value) => setSelectedAgentIndex(String(value))}
          />
          <TickAgentParamCard agent={activeAgent} agentIndex={activeIndex} />
        </>
      ) : (
        <span className="showcase-agent-empty">暂无智能体参数</span>
      )}
    </article>
  )
}

function TickAgentParamCard({
  agent,
  agentIndex,
}: {
  agent: TickAgentRunParams
  agentIndex: number
}) {
  return (
    <div className="showcase-agent-card">
      <div className="showcase-agent-card__head">
        <div>
          <strong>{formatAgentName(agent.agent_name)}</strong>
          <span>第 {agentIndex + 1} 组输入参数</span>
        </div>
        <Tag>{formatSideName(agent.side)}</Tag>
      </div>
      <div className="showcase-agent-param-grid">
        {Object.entries(agent.params ?? {}).map(([key, value]) => (
          <div key={key}>
            <Text>{formatParamName(key)}</Text>
            <strong>{formatParamValue(value)}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <Text>{label}</Text>
      <strong>{value}</strong>
    </div>
  )
}

function formatBranchName(branchId: number | undefined) {
  if (typeof branchId !== 'number') {
    return '未命名分支'
  }
  return branchNameMap[branchId] ?? `分支 ${branchId}`
}

function formatAgentName(agentName: string) {
  return agentNameMap[agentName] ?? agentName
}

function formatParamName(paramName: string) {
  return paramNameMap[paramName] ?? paramName
}

function formatSideName(side: string) {
  return side ? sideNameMap[side] ?? side : '-'
}

function formatParamValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => formatParamItem(item)).join('、') || '-'
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  if (value === null || value === undefined || value === '') {
    return '-'
  }
  if (typeof value === 'string') {
    return formatParamItem(value)
  }
  if (typeof value === 'object') {
    const keys = Object.keys(asRecord(value))
    return keys.length ? `结构化数据 ${keys.length} 项` : '-'
  }
  return String(value)
}

function formatParamItem(value: unknown) {
  if (typeof value !== 'string') {
    return String(value)
  }
  return sideNameMap[value] ?? value
}

function formatMetricName(
  metricKey: string,
  aggregateByKey?: Map<string, RunMetricAggregate>,
) {
  return aggregateByKey?.get(metricKey)?.name ?? metricNameMap[metricKey] ?? '补充指标'
}

function formatCallbackName(callbackName: string) {
  return callbackNameMap[callbackName] ?? 'Callback 报告'
}

function formatSimulationMetricValue(
  value: SimulationMetricValue,
  aggregate?: Pick<RunMetricAggregate, 'key' | 'name'>,
) {
  if (value === undefined || value === null || value === '') {
    return '暂无'
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  if (typeof value === 'number') {
    return aggregate ? formatMetricValue(value, aggregate) : formatUnknownMetricValue(value)
  }
  if (typeof value === 'string') {
    return formatParamItem(value)
  }
  const samples = metricSamples(value)
  if (samples.length) {
    const sampleMean = samples.reduce((total, item) => total + item, 0) / samples.length
    return aggregate ? formatMetricValue(sampleMean, aggregate) : formatUnknownMetricValue(sampleMean)
  }
  const keys = Object.keys(asRecord(value))
  return keys.length ? `结构化数据 ${keys.length} 项` : '暂无'
}

function formatUnknownMetricValue(value: unknown) {
  if (typeof value === 'number') {
    return String(Number(value.toFixed(3)))
  }
  return formatParamValue(value)
}

function formatStopReason(stopReason: string) {
  const stopReasonMap: Record<string, string> = {
    env_terminal: '环境终止',
    env_truncated: '达到最大步数',
    max_steps: '达到最大步数',
    timeout: '运行超时',
  }
  return stopReason ? stopReasonMap[stopReason] ?? '其他停止原因' : '-'
}

function formatElapsedSeconds(value: number | undefined) {
  return typeof value === 'number' ? `${Number(value.toFixed(2))} 秒` : '-'
}

function formatDamageRatioFromTarget(initialHealth: unknown, healthDelta: unknown) {
  if (typeof initialHealth !== 'number' || typeof healthDelta !== 'number' || initialHealth <= 0) {
    return '暂无'
  }
  const ratio = Math.min(1, Math.max(0, -healthDelta / initialHealth))
  return `${Math.round(ratio * 1000) / 10}%`
}

function metricSamples(value: unknown): number[] {
  if (typeof value === 'boolean') {
    return []
  }
  if (typeof value === 'number') {
    return [value]
  }
  if (isNumericRecord(value)) {
    return Object.values(value)
  }
  return []
}

function isNumericRecord(value: unknown): value is Record<string, number> {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value) &&
    Object.values(value).length > 0 &&
    Object.values(value).every((item) => typeof item === 'number')
  )
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function iterationTitle(iteration: RunIterationOutput) {
  return iteration.iteration_tags[0]?.label ?? `第 ${iteration.iteration_index + 1} 轮`
}

function getPreviousIteration(
  runOutput: RunOutput,
  selectedIteration: RunIterationOutput,
) {
  const selectedIndex = runOutput.iterations.findIndex(
    (iteration) => iteration.iteration_index === selectedIteration.iteration_index,
  )
  return selectedIndex > 0 ? runOutput.iterations[selectedIndex - 1] : undefined
}

function formatDuration(startedAt: string, endedAt: string | null, now: number) {
  const startTime = Date.parse(startedAt)
  if (Number.isNaN(startTime)) {
    return '-'
  }
  const endTime = endedAt ? Date.parse(endedAt) : now
  if (Number.isNaN(endTime) || endTime < startTime) {
    return '-'
  }
  const totalSeconds = Math.floor((endTime - startTime) / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}时 ${minutes}分 ${seconds}秒`
  }
  if (minutes > 0) {
    return `${minutes}分 ${seconds}秒`
  }
  return `${seconds}秒`
}

function formatMetricValue(value: number, aggregate?: Pick<RunMetricAggregate, 'key' | 'name'>) {
  if (aggregate && isRatioMetric(aggregate)) {
    return `${Math.round(value * 1000) / 10}%`
  }
  return String(Number(value.toFixed(3)))
}

function isRatioMetric(aggregate: Pick<RunMetricAggregate, 'key' | 'name'>) {
  return (
    aggregate.key.includes('ratio') ||
    aggregate.key.includes('rate') ||
    aggregate.name.includes('比例') ||
    aggregate.name.includes('率')
  )
}

function metricMeanChange(
  currentAggregate: RunMetricAggregate,
  previousAggregate: RunMetricAggregate | undefined,
) {
  if (!previousAggregate) {
    return {
      className: 'showcase-delta--flat',
      text: '首轮基线',
    }
  }
  const diff = currentAggregate.mean - previousAggregate.mean
  if (Math.abs(diff) < 0.0005) {
    return {
      className: 'showcase-delta--flat',
      text: '较上一轮持平',
    }
  }
  const sign = diff > 0 ? '+' : ''
  return {
    className: diff > 0 ? 'showcase-delta--good' : 'showcase-delta--warn',
    text: `较上一轮 ${sign}${formatMetricValue(diff, currentAggregate)}`,
  }
}

function metricVariance(aggregate: RunMetricAggregate) {
  return Number((aggregate.std ** 2).toFixed(6))
}

function formatVarianceValue(value: number) {
  if (value === 0) {
    return '0'
  }
  if (Math.abs(value) < 0.001) {
    return value.toFixed(6)
  }
  return String(Number(value.toFixed(3)))
}

function buildMetricTrendOption(
  trend: RunMetricTrend,
  selectedIterationIndex: number,
): EChartsCoreOption {
  const ratioMetric = isRatioMetric(trend)
  return {
    animationDuration: 320,
    grid: {
      bottom: 30,
      containLabel: true,
      left: 8,
      right: 14,
      top: 20,
    },
    tooltip: {
      backgroundColor: 'rgba(250, 249, 245, 0.96)',
      borderColor: '#e8e6dc',
      confine: true,
      textStyle: {
        color: '#3d3d3a',
        fontSize: 12,
      },
      trigger: 'axis',
      valueFormatter: (value: unknown) =>
        typeof value === 'number'
          ? formatMetricValue(value, trend)
          : String(value),
    },
    xAxis: {
      axisLabel: {
        color: '#87867f',
        fontSize: 12,
      },
      axisLine: {
        lineStyle: {
          color: '#e8e6dc',
        },
      },
      axisTick: {
        show: false,
      },
      boundaryGap: false,
      data: trend.points.map((point) => `第${point.iteration_index + 1}轮`),
      type: 'category',
    },
    yAxis: {
      axisLabel: {
        color: '#87867f',
        fontSize: 12,
        formatter: (value: number) =>
          ratioMetric ? `${Math.round(value * 100)}%` : String(value),
      },
      splitLine: {
        lineStyle: {
          color: '#f0eee6',
        },
      },
      type: 'value',
    },
    series: [
      {
        areaStyle: {
          color: 'rgba(201, 100, 66, 0.1)',
        },
        data: trend.points.map((point) => ({
          value: point.mean,
          itemStyle:
            point.iteration_index === selectedIterationIndex
              ? {
                  borderColor: '#141413',
                  borderWidth: 3,
                  color: '#c96442',
                }
              : {
                  color: '#c96442',
                },
          symbolSize: point.iteration_index === selectedIterationIndex ? 12 : 7,
        })),
        emphasis: {
          focus: 'series',
        },
        lineStyle: {
          color: '#c96442',
          width: 3,
        },
        name: trend.name,
        smooth: true,
        symbol: 'circle',
        type: 'line',
      },
    ],
  }
}

function statusText(status: string) {
  const statusMap: Record<string, string> = {
    created: '已创建',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return statusMap[status] ?? status
}

function statusColor(status: string) {
  if (status === 'completed') {
    return 'success'
  }
  if (status === 'failed') {
    return 'error'
  }
  if (status === 'running') {
    return 'processing'
  }
  return 'default'
}

export default SimulationShowcasePage
