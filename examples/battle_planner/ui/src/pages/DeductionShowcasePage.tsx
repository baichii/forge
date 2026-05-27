import {
  AimOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  DashboardOutlined,
  DeploymentUnitOutlined,
  FastForwardOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  RadarChartOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { Button, Card, Progress, Select, Space, Tag, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { deductionShowcaseView } from '../mocks/deductionShowcase'
import type {
  DeductionMetric,
  DeductionStatusTone,
} from '../types/deductionShowcase'
import './DeductionShowcasePage.css'

const { Paragraph, Text, Title } = Typography

const playbackSpeeds = ['0.5x', '1x', '2x', '4x']

function DeductionShowcasePage() {
  const view = deductionShowcaseView
  const [selectedSessionId, setSelectedSessionId] = useState(view.sessions[0]?.id)
  const selectedSession = useMemo(
    () =>
      view.sessions.find((session) => session.id === selectedSessionId) ??
      view.sessions[0],
    [selectedSessionId, view.sessions],
  )
  const [selectedRoundId, setSelectedRoundId] = useState(
    selectedSession?.rounds.at(-1)?.id,
  )
  const selectedRound = useMemo(
    () =>
      selectedSession?.rounds.find((round) => round.id === selectedRoundId) ??
      selectedSession?.rounds.at(-1),
    [selectedRoundId, selectedSession],
  )
  const [isPaused, setIsPaused] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState('1x')
  const [visibleEventCount, setVisibleEventCount] = useState(1)
  const playbackDone =
    !!selectedRound && visibleEventCount >= selectedRound.events.length
  const selectedStage = useMemo(
    () => {
      if (!selectedRound) {
        return undefined
      }
      const stageIndex = Math.min(
        Math.max(visibleEventCount - 1, 0),
        selectedRound.stages.length - 1,
      )
      return selectedRound.stages[stageIndex]
    },
    [selectedRound, visibleEventCount],
  )
  const visibleEvents = selectedRound?.events.slice(0, visibleEventCount) ?? []

  useEffect(() => {
    if (!selectedRound || isPaused || playbackDone) {
      return undefined
    }
    const timer = window.setTimeout(() => {
      setVisibleEventCount((count) =>
        Math.min(count + 1, selectedRound.events.length),
      )
    }, 1300 / playbackSpeedValue(playbackSpeed))

    return () => window.clearTimeout(timer)
  }, [isPaused, playbackDone, playbackSpeed, selectedRound, visibleEventCount])

  const resetPlayback = () => {
    setVisibleEventCount(1)
    setIsPaused(false)
  }

  const handleSessionChange = (sessionId: string) => {
    const nextSession =
      view.sessions.find((session) => session.id === sessionId) ?? view.sessions[0]
    setSelectedSessionId(nextSession?.id)
    setSelectedRoundId(nextSession?.rounds.at(-1)?.id)
    resetPlayback()
  }

  const handleRoundChange = (roundId: string) => {
    setSelectedRoundId(roundId)
    resetPlayback()
  }

  if (!selectedSession || !selectedRound || !selectedStage) {
    return null
  }

  return (
    <main className="deduction-page">
      <section className="deduction-head" aria-labelledby="deduction-title">
        <div>
          <Tag className="deduction-eyebrow">Deduction Replay</Tag>
          <Title id="deduction-title" level={1}>
            回放单轮策略
            <br />
            在推演中的效果。
          </Title>
          <Paragraph>
            选择历史推演和策略轮次，按时间戳回放态势变化、指标表现、事件日志和执行要点。
          </Paragraph>
        </div>
        <span className="deduction-head__tag">
          {selectedSession.displayName} · {selectedRound.label}
        </span>
      </section>

      <section className="deduction-layout" aria-label="推演展示工作区">
        <Card className="deduction-side" variant="borderless">
          <div className="deduction-side__head">
            <div>
              <Text strong>推演控制</Text>
              <Text>选择历史推演与轮次</Text>
            </div>
            <DashboardOutlined />
          </div>

          <div className="deduction-field">
            <Text strong>历史推演 session</Text>
            <Select
              value={selectedSession.id}
              onChange={handleSessionChange}
              options={view.sessions.map((session) => ({
                value: session.id,
                label: session.displayName,
              }))}
            />
          </div>

          <div className="deduction-field">
            <Text strong>策略轮次</Text>
            <Select
              value={selectedRound.id}
              onChange={handleRoundChange}
              options={selectedSession.rounds.map((round) => ({
                value: round.id,
                label: `${round.label} · ${round.version}`,
              }))}
            />
          </div>

          <div className="deduction-strategy-card">
            <Tag color={tagColor(selectedRound.statusTone)} icon={<CheckCircleFilled />}>
              {selectedRound.status}
            </Tag>
            <strong>{selectedSession.strategy.name}</strong>
            <span>{selectedSession.strategy.description}</span>
            <span>{selectedRound.version}</span>
          </div>

          <div className="deduction-replay-control" aria-label="推演回放控制">
            <div className="deduction-replay-control__head">
              <Text strong>回放控制</Text>
              <Tag color={playbackDone ? 'success' : isPaused ? 'default' : 'processing'}>
                {playbackDone ? '回放结束' : isPaused ? '已暂停' : '播放中'}
              </Tag>
            </div>
            <Button
              block
              icon={
                playbackDone || isPaused ? (
                  <PlayCircleOutlined />
                ) : (
                  <PauseCircleOutlined />
                )
              }
              onClick={() => {
                if (playbackDone) {
                  setVisibleEventCount(1)
                  setIsPaused(false)
                  return
                }
                setIsPaused((value) => !value)
              }}
            >
              {playbackDone ? '重新回放' : isPaused ? '继续回放' : '暂停回放'}
            </Button>
            <div className="deduction-speed-list">
              {playbackSpeeds.map((speed) => (
                <button
                  className={
                    playbackSpeed === speed
                      ? 'deduction-speed-button deduction-speed-button--active'
                      : 'deduction-speed-button'
                  }
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  type="button"
                >
                  {speed === '4x' ? <FastForwardOutlined /> : null}
                  <span>{speed}</span>
                </button>
              ))}
            </div>
            <div className="deduction-replay-progress">
              <Text>日志进度</Text>
              <strong>
                {visibleEventCount} / {selectedRound.events.length}
              </strong>
            </div>
          </div>
        </Card>

        <Card className="deduction-main-panel" variant="borderless">
          <section className="deduction-effect-overview">
            <div>
              <Tag className="deduction-eyebrow">方案指标总览</Tag>
              <Title level={2}>{selectedRound.effect.title}</Title>
              <Paragraph>{selectedRound.effect.summary}</Paragraph>
            </div>
            <div className="deduction-progress-card">
              <Text>当前时间</Text>
              <strong>
                {visibleEvents.at(-1)?.time ?? selectedRound.effect.currentTime}
              </strong>
              <Progress
                percent={Number.parseInt(selectedRound.effect.progress, 10)}
                showInfo={false}
                strokeColor="#c96442"
              />
              <span>计划完成度 {selectedRound.effect.progress}</span>
            </div>
          </section>

          <section className="deduction-metric-grid" aria-label="推演指标">
            {selectedRound.metrics.map((metric) => (
              <MetricCard key={metric.label} metric={metric} />
            ))}
          </section>

          <section className="deduction-situation" aria-label="态势展示">
            <div className="deduction-section-title">
              <span>
                <RadarChartOutlined /> 态势视图
              </span>
              <Text>
                {isPaused ? '暂停' : '回放'} · {playbackSpeed}
              </Text>
            </div>

            <div className="deduction-map-board">
              <div className="deduction-route deduction-route--air" />
              <div className="deduction-route deduction-route--sea" />
              <span className="deduction-marker deduction-marker--air">
                空中编队
              </span>
              <span className="deduction-marker deduction-marker--ship">
                舰艇编队
              </span>
              <span className="deduction-marker deduction-marker--target">
                关键目标
              </span>
              <span className="deduction-window">有效压制窗口</span>
              <article className="deduction-stage-detail">
                <Tag color={tagColor(selectedStage.statusTone)}>
                  {selectedStage.status}
                </Tag>
                <Text>{selectedStage.time}</Text>
                <Title level={3}>{selectedStage.title}</Title>
                <Paragraph>{selectedStage.description}</Paragraph>
              </article>
            </div>
          </section>

          <section className="deduction-bottom-grid">
            <article className="deduction-events">
              <div className="deduction-section-title">
                <span>
                  <ClockCircleOutlined /> 事件流
                </span>
                <Text>最近关键事件</Text>
              </div>
              <div className="deduction-event-list">
                {visibleEvents.map((event) => (
                  <div className="deduction-event" key={`${event.time}-${event.title}`}>
                    <Tag color={tagColor(event.tone)}>{event.time}</Tag>
                    <div>
                      <strong>{event.title}</strong>
                      <span>{event.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="deduction-agents">
              <div className="deduction-section-title">
                <span>
                  <DeploymentUnitOutlined /> 执行要点
                </span>
                <Text>智能体业务状态</Text>
              </div>
              <div className="deduction-agent-list">
                {selectedRound.agents.map((agent) => (
                  <div className="deduction-agent" key={agent.name}>
                    <Space>
                      <AimOutlined />
                      <Text strong>{agent.name}</Text>
                    </Space>
                    <span>{agent.role}</span>
                    <strong>{agent.status}</strong>
                    <p>{agent.summary}</p>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="deduction-objective">
            <SafetyCertificateOutlined />
            <Text>{selectedSession.strategy.objective}</Text>
          </section>
        </Card>
      </section>
    </main>
  )
}

function MetricCard({ metric }: { metric: DeductionMetric }) {
  return (
    <article className={`deduction-metric deduction-metric--${metric.tone}`}>
      <Text>{metric.label}</Text>
      <strong>{metric.value}</strong>
      <span>{metric.trend}</span>
    </article>
  )
}

function tagColor(tone: DeductionStatusTone) {
  if (tone === 'success') {
    return 'success'
  }
  if (tone === 'processing') {
    return 'processing'
  }
  if (tone === 'warning') {
    return 'warning'
  }
  return 'default'
}

function playbackSpeedValue(speed: string) {
  return Number.parseFloat(speed.replace('x', '')) || 1
}

export default DeductionShowcasePage
