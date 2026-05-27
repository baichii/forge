import {
  CheckCircleFilled,
  DashboardOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  LineChartOutlined,
  SlidersOutlined,
} from '@ant-design/icons'
import { Card, Select, Space, Tabs, Tag, Typography } from 'antd'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import type {
  ECharts,
  EChartsCoreOption,
} from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useMemo, useRef, useState } from 'react'
import { strategyIterationReplay } from '../mocks/replays/strategyIteration'
import type {
  ReplayDataSupportItem,
  ReplayRound,
  StrategyIterationReplay,
} from '../types/iterationReplay'
import './SimulationShowcasePage.css'

const { Paragraph, Text, Title } = Typography

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

function SimulationShowcasePage() {
  const replay = strategyIterationReplay
  const [selectedRoundId, setSelectedRoundId] = useState(replay.recommendedRoundId)

  const selectedRound = useMemo(
    () =>
      replay.rounds.find((round) => round.roundId === selectedRoundId) ??
      replay.rounds.at(-1),
    [replay.rounds, selectedRoundId],
  )
  const previousRound = useMemo(() => {
    if (!selectedRound) {
      return undefined
    }
    const index = replay.rounds.findIndex(
      (round) => round.roundId === selectedRound.roundId,
    )
    return index > 0 ? replay.rounds[index - 1] : undefined
  }, [replay.rounds, selectedRound])

  if (!selectedRound) {
    return null
  }

  return (
    <main className="showcase-page">
      <section className="showcase-head" aria-labelledby="showcase-title">
        <div>
          <Tag className="showcase-eyebrow">Strategy Iteration</Tag>
          <Title id="showcase-title" level={1}>
            让每轮策略优化都有据可循。
          </Title>
          <Paragraph className="showcase-lead">
            围绕历史推演记录查看多轮策略调整、关键指标趋势、执行参数变化和推荐轮次依据。
          </Paragraph>
        </div>
        <span className="showcase-head__tag">
          历史推演 · {replay.selectedSession.totalRounds} 轮迭代记录
        </span>
      </section>

      <section className="showcase-layout" aria-label="策略迭代工作区">
        <Card className="showcase-panel" variant="borderless">
          <div className="showcase-panel__head">
            <div>
              <Text strong>策略与轮次</Text>
              <Text>选择历史推演记录并切换轮次报告</Text>
            </div>
            <DashboardOutlined />
          </div>

          <div className="showcase-field">
            <Text strong>已配置策略</Text>
            <Select
              value={replay.configuredStrategy.id}
              options={[
                {
                  value: replay.configuredStrategy.id,
                  label: replay.configuredStrategy.name,
                },
              ]}
            />
          </div>

          <div className="showcase-field">
            <Text strong>历史推演记录</Text>
            <Select
              value={replay.selectedSession.sessionId}
              options={[
                {
                  value: replay.selectedSession.sessionId,
                  label: replay.selectedSession.displayName,
                },
              ]}
            />
          </div>

          <div className="showcase-session-card">
            <Tag color="success">{statusText(replay.selectedSession.status)}</Tag>
            <strong>{replay.configuredStrategy.name}</strong>
            <span>{replay.configuredStrategy.description}</span>
            <span>
              {replay.selectedSession.totalRounds} 轮 · 每轮并行{' '}
              {replay.selectedSession.seedCount} 局 · {replay.selectedSession.stopReason}
            </span>
          </div>

          <div className="showcase-round-list" aria-label="策略轮次列表">
            {replay.rounds.map((round) => (
              <button
                className={
                  round.roundId === selectedRound.roundId
                    ? 'showcase-round-button showcase-round-button--active'
                    : 'showcase-round-button'
                }
                key={round.roundId}
                type="button"
                onClick={() => setSelectedRoundId(round.roundId)}
              >
                <span>R{round.roundNumber}</span>
                <strong>{round.label}</strong>
                <em>{round.metrics.score}</em>
              </button>
            ))}
          </div>
        </Card>

        <Card className="showcase-detail" variant="borderless">
          <SessionDescription replay={replay} />
          <TrendPanel
            rounds={replay.rounds}
            selectedRound={selectedRound}
            onRoundSelect={setSelectedRoundId}
          />
          <RoundReport
            replay={replay}
            selectedRound={selectedRound}
            previousRound={previousRound}
          />
        </Card>
      </section>
    </main>
  )
}

function SessionDescription({ replay }: { replay: StrategyIterationReplay }) {
  return (
    <section className="showcase-session-brief" aria-label="策略实现要素">
      <div className="showcase-session-brief__head">
        <div>
          <Tag className="showcase-eyebrow">策略实现要素</Tag>
          <Title level={2}>{replay.implementation.title}</Title>
          <Paragraph>{replay.implementation.description}</Paragraph>
        </div>
        <span>{replay.selectedSession.displayName}</span>
      </div>

      <div className="showcase-implementation-grid">
        {replay.implementation.items.map((item) => (
          <article key={item.label}>
            <Text>{item.label}</Text>
            <strong>{item.value}</strong>
          </article>
        ))}
      </div>
    </section>
  )
}

function TrendPanel({
  rounds,
  selectedRound,
  onRoundSelect,
}: {
  rounds: ReplayRound[]
  selectedRound: ReplayRound
  onRoundSelect: (roundId: string) => void
}) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<ECharts | null>(null)
  const selectedIndex = rounds.findIndex(
    (round) => round.roundId === selectedRound.roundId,
  )

  useEffect(() => {
    const chartElement = chartRef.current
    if (!chartElement) {
      return undefined
    }

    const chart =
      echarts.getInstanceByDom(chartElement) ??
      echarts.init(chartElement, undefined, { renderer: 'canvas' })
    chartInstanceRef.current = chart
    chart.setOption(buildTrendOption(rounds, selectedRound.roundId), {
      notMerge: true,
    })

    const handleCanvasClick = (event: { offsetX: number; offsetY: number }) => {
      const converted = chart.convertFromPixel(
        { xAxisIndex: 0 },
        [event.offsetX, event.offsetY],
      )
      const rawIndex = Array.isArray(converted) ? converted[0] : converted
      if (typeof rawIndex !== 'number' || Number.isNaN(rawIndex)) {
        return
      }

      const dataIndex = Math.max(0, Math.min(rounds.length - 1, Math.round(rawIndex)))
      const round = rounds[dataIndex]
      if (round) {
        onRoundSelect(round.roundId)
      }
    }

    chart.getZr().on('click', handleCanvasClick)

    let resizeFrame = 0
    const resizeObserver = new ResizeObserver(() => {
      window.cancelAnimationFrame(resizeFrame)
      resizeFrame = window.requestAnimationFrame(() => {
        chart.resize()
      })
    })
    resizeObserver.observe(chartElement)

    return () => {
      chart.getZr().off('click', handleCanvasClick)
      window.cancelAnimationFrame(resizeFrame)
      resizeObserver.disconnect()
    }
  }, [onRoundSelect, rounds, selectedRound.roundId])

  useEffect(
    () => () => {
      chartInstanceRef.current?.dispose()
      chartInstanceRef.current = null
    },
    [],
  )

  return (
    <div className="showcase-timeline" aria-label="多轮关键指标变化">
      <div className="showcase-section-title">
        <span>
          <LineChartOutlined /> 多局指标变化
        </span>
        <Text>综合评分均值趋势 · 基线 / 探索 / 当前最佳 / 推荐方案</Text>
      </div>
      <div className="showcase-trend-strip" aria-label="当前轮聚合指标">
        <span>
          当前轮 <strong>R{selectedRound.roundNumber}</strong>
        </span>
        <span>
          综合评分均值 <strong>{selectedRound.seedStats.meanScore}</strong>
        </span>
        <span>
          最好 / 最差{' '}
          <strong>
            {selectedRound.seedStats.bestScore} / {selectedRound.seedStats.worstScore}
          </strong>
        </span>
        <span>
          成功率 <strong>{formatPercent(selectedRound.seedStats.successRate)}</strong>
        </span>
        <span>
          波动 <strong>{selectedRound.seedStats.stdScore}</strong>
        </span>
        <span>
          轮次位置 <strong>{selectedIndex + 1} / {rounds.length}</strong>
        </span>
      </div>
      <div className="showcase-line-chart-wrap">
        <div
          ref={chartRef}
          className="showcase-line-chart"
          role="img"
          aria-label="15 轮综合评分均值、最好值和最差值折线图"
        />
        <div
          className="showcase-chart-hit-layer"
          style={{
            gridTemplateColumns: `repeat(${rounds.length}, minmax(0, 1fr))`,
          }}
        >
          {rounds.map((round) => (
            <button
              aria-label={`查看第 ${round.roundNumber} 轮`}
              key={round.roundId}
              onClick={() => onRoundSelect(round.roundId)}
              title={`R${round.roundNumber} · ${round.label}`}
              type="button"
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function RoundReport({
  replay,
  selectedRound,
  previousRound,
}: {
  replay: StrategyIterationReplay
  selectedRound: ReplayRound
  previousRound?: ReplayRound
}) {
  return (
    <div className="showcase-round-detail">
      <div className="showcase-round-head">
        <div>
          <Text>当前轮效果</Text>
          <Title level={3}>
            Round {String(selectedRound.roundNumber).padStart(2, '0')} /{' '}
            {selectedRound.label}
          </Title>
          <Paragraph>{selectedRound.summary}</Paragraph>
        </div>
        <Tag color={decisionColor(selectedRound.decision.status)}>
          {selectedRound.decision.recommendation}
        </Tag>
      </div>

      <div className="showcase-metrics">
        <Metric
          label="综合评分"
          value={selectedRound.metrics.score}
          delta={metricDelta(
            selectedRound.metrics.score,
            previousRound?.metrics.score,
            'higher',
          )}
        />
        <Metric
          label="目标毁伤"
          value={formatPercent(selectedRound.metrics.targetDamageRatio)}
          delta={metricDelta(
            selectedRound.metrics.targetDamageRatio,
            previousRound?.metrics.targetDamageRatio,
            'higher',
            true,
          )}
        />
        <Metric
          label="武器消耗"
          value={formatPercent(selectedRound.metrics.weaponCostRatio)}
          delta={metricDelta(
            selectedRound.metrics.weaponCostRatio,
            previousRound?.metrics.weaponCostRatio,
            'lower',
            true,
          )}
        />
        <Metric
          label="平台暴露"
          value={formatPercent(selectedRound.metrics.platformRiskRatio)}
          delta={metricDelta(
            selectedRound.metrics.platformRiskRatio,
            previousRound?.metrics.platformRiskRatio,
            'lower',
            true,
          )}
        />
      </div>

      <div className="showcase-detail-grid">
        <article>
          <Space>
            <FileTextOutlined />
            <Text strong>仿真报告摘要</Text>
          </Space>
          <Paragraph>{selectedRound.reportSummary}</Paragraph>
        </article>
        <article>
          <Space>
            <ExperimentOutlined />
            <Text strong>智能分析与建议</Text>
          </Space>
          <Paragraph>{selectedRound.llmDiagnosis}</Paragraph>
        </article>
        <article>
          <Text strong>相对上一轮优化</Text>
          <div className="showcase-diff-list">
            {selectedRound.parameterDiff.map((item) => (
              <span key={item.name}>
                <CheckCircleFilled /> {item.name}：{item.reason}
              </span>
            ))}
          </div>
        </article>
        <article>
          <Text strong>效果结论</Text>
          <Paragraph>{selectedRound.decision.rationale}</Paragraph>
        </article>
      </div>
      <Tabs
        className="showcase-secondary-tabs"
        items={[
          {
            key: 'execution',
            label: '运行参数',
            children: <ExecutionPanel selectedRound={selectedRound} />,
          },
          {
            key: 'seeds',
            label: '多局结果',
            children: <SeedPanel selectedRound={selectedRound} />,
          },
          {
            key: 'support',
            label: '数据来源说明',
            children: <DataSupportPanel items={replay.dataSupport} />,
          },
        ]}
      />
    </div>
  )
}

function ExecutionPanel({ selectedRound }: { selectedRound: ReplayRound }) {
  return (
    <div className="showcase-execution">
      <div className="showcase-section-title">
        <span>
          <SlidersOutlined /> 当前轮运行参数
        </span>
        <Text>{selectedRound.executionPlan.planName}</Text>
      </div>

      <div className="showcase-execution-grid">
        <Info label="执行时间窗" value={selectedRound.executionPlan.timeWindowSummary} />
        <Info label="目标对象" value={selectedRound.executionPlan.targets.join('、')} />
        <Info label="武器配置" value={selectedRound.executionPlan.weaponSummary} />
        <Info
          label="计划/触发动作"
          value={`${selectedRound.executionPlan.plannedActionCount} / ${selectedRound.executionPlan.dispatchedActionCount}`}
        />
        <Info
          label="参与智能体"
          value={selectedRound.executionPlan.agents.join('、')}
        />
        <Info
          label="最大仿真步数"
          value={`${selectedRound.executionPlan.maxSimulationSteps}`}
        />
      </div>

      <div className="showcase-param-table">
        <div className="showcase-param-row showcase-param-row--head">
          <span>参数</span>
          <span>上一轮</span>
          <span>当前轮</span>
          <span>变化解释</span>
        </div>
        {selectedRound.parameterDiff.map((item) => (
          <div className="showcase-param-row" key={`${item.name}-${item.currentValue}`}>
            <span>{item.name}</span>
            <span>{item.previousValue}</span>
            <span>{item.currentValue}</span>
            <span>{item.impact}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SeedPanel({ selectedRound }: { selectedRound: ReplayRound }) {
  return (
    <div className="showcase-seed-panel">
      <div className="showcase-section-title">
        <span>
          <ExperimentOutlined /> 多局稳定性
        </span>
        <Text>多局聚合结果，单局结果不作为独立轮次</Text>
      </div>
      <div className="showcase-seed-grid">
        <Metric label="并行局数" value={selectedRound.seedStats.seedCount} />
        <Metric label="平均评分" value={selectedRound.seedStats.meanScore} />
        <Metric label="最好 / 最差" value={`${selectedRound.seedStats.bestScore} / ${selectedRound.seedStats.worstScore}`} />
        <Metric label="波动" value={`${selectedRound.seedStats.stdScore} · ${selectedRound.seedStats.volatilityLevel}`} />
      </div>
      <div className="showcase-seed-runs" aria-label="单局推演结果">
        {selectedRound.seedRuns.map((run) => (
          <span key={run.seed}>
            <strong>第 {run.seed} 局</strong>
            <em>{run.score}</em>
            {run.success ? '通过' : run.failureReason}
          </span>
        ))}
      </div>
      <div className="showcase-failure-list">
        {selectedRound.seedStats.failureReasons.map((item) => (
          <span key={item.reason}>
            <strong>{item.reason}</strong>
            <em>{item.count} 次</em>
            {item.summary}
          </span>
        ))}
      </div>
    </div>
  )
}

function DataSupportPanel({ items }: { items: ReplayDataSupportItem[] }) {
  return (
    <div className="showcase-support-panel">
      {items.map((item) => (
        <article key={item.label}>
          <Tag color={supportColor(item.support)}>{supportText(item.support)}</Tag>
          <strong>{item.label}</strong>
          <span>{item.source}</span>
          <p>{item.note}</p>
        </article>
      ))}
    </div>
  )
}

function Metric({
  delta,
  label,
  value,
}: {
  delta?: { text: string; tone: string }
  label: string
  value: string | number
}) {
  return (
    <div>
      <Text>{label}</Text>
      <strong>{value}</strong>
      {delta ? (
        <small className={`showcase-delta showcase-delta--${delta.tone}`}>
          {delta.text}
        </small>
      ) : null}
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

function metricDelta(
  current: number,
  previous: number | undefined,
  better: 'higher' | 'lower',
  asPercent = false,
) {
  if (previous === undefined) {
    return undefined
  }
  const diff = current - previous
  if (diff === 0) {
    return { text: '持平', tone: 'flat' }
  }
  const improved = better === 'higher' ? diff > 0 : diff < 0
  const sign = diff > 0 ? '+' : ''
  const value = asPercent ? `${sign}${Math.round(diff * 100)}%` : `${sign}${diff}`
  return {
    text: `${value} 较上一轮`,
    tone: improved ? 'good' : 'warn',
  }
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function buildTrendOption(
  rounds: ReplayRound[],
  selectedRoundId: string,
): EChartsCoreOption {
  const xAxisData = rounds.map((round) => `R${round.roundNumber}`)
  const meanScores = rounds.map((round) => ({
    value: round.seedStats.meanScore,
    itemStyle:
      round.roundId === selectedRoundId
        ? {
            borderColor: '#141413',
            borderWidth: 3,
            color: '#c96442',
          }
        : {
            color: '#c96442',
          },
    symbolSize: round.roundId === selectedRoundId ? 12 : 7,
  }))

  return {
    animationDuration: 320,
    grid: {
      bottom: 30,
      containLabel: true,
      left: 8,
      right: 14,
      top: 16,
    },
    tooltip: {
      axisPointer: {
        lineStyle: {
          color: '#c96442',
          type: 'dashed',
        },
      },
      backgroundColor: 'rgba(250, 249, 245, 0.96)',
      borderColor: '#e8e6dc',
      confine: true,
      textStyle: {
        color: '#3d3d3a',
        fontSize: 12,
      },
      trigger: 'axis',
    },
    xAxis: {
      axisLabel: {
        color: '#87867f',
        fontSize: 12,
        interval: 0,
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
      data: xAxisData,
      type: 'category',
    },
    yAxis: {
      axisLabel: {
        color: '#87867f',
        fontSize: 12,
      },
      max: ({ max }: { max: number }) => Math.min(100, Math.ceil(max + 4)),
      min: ({ min }: { min: number }) => Math.max(0, Math.floor(min - 4)),
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
        data: meanScores,
        emphasis: {
          focus: 'series',
        },
        lineStyle: {
          color: '#c96442',
          width: 3,
        },
        name: '综合评分均值',
        smooth: true,
        symbol: 'circle',
        type: 'line',
      },
      {
        data: rounds.map((round) => round.seedStats.bestScore),
        lineStyle: {
          color: '#16823a',
          type: 'dashed',
          width: 1.5,
        },
        name: '最好值',
        showSymbol: false,
        smooth: true,
        type: 'line',
      },
      {
        data: rounds.map((round) => round.seedStats.worstScore),
        lineStyle: {
          color: '#87867f',
          type: 'dashed',
          width: 1.5,
        },
        name: '最差值',
        showSymbol: false,
        smooth: true,
        type: 'line',
      },
    ],
  }
}

function statusText(status: string) {
  if (status === 'completed') {
    return '已完成'
  }
  return status
}

function decisionColor(status: string) {
  if (status === 'recommended' || status === 'current_best') {
    return 'success'
  }
  if (status === 'rollback' || status === 'negative_sample') {
    return 'warning'
  }
  return 'processing'
}

function supportText(support: ReplayDataSupportItem['support']) {
  if (support === 'direct') {
    return '直接支持'
  }
  if (support === 'derived') {
    return '转换获取'
  }
  return '暂不支持'
}

function supportColor(support: ReplayDataSupportItem['support']) {
  if (support === 'direct') {
    return 'success'
  }
  if (support === 'derived') {
    return 'processing'
  }
  return 'warning'
}

export default SimulationShowcasePage
