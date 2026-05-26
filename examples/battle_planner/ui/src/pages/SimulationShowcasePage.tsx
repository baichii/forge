import {
  DashboardOutlined,
  LinkOutlined,
  RadarChartOutlined,
} from '@ant-design/icons'
import { Card, Empty, Select, Space, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { ConfiguredStrategy } from '../types/strategy'
import { readConfiguredStrategies } from '../utils/configuredStrategies'
import './SimulationShowcasePage.css'

const { Paragraph, Text, Title } = Typography

function SimulationShowcasePage() {
  const [configuredStrategies] = useState<ConfiguredStrategy[]>(() =>
    readConfiguredStrategies(),
  )
  const [selectedId, setSelectedId] = useState(configuredStrategies[0]?.id)

  const selectedStrategy = useMemo(
    () =>
      configuredStrategies.find((strategy) => strategy.id === selectedId) ??
      configuredStrategies[0],
    [configuredStrategies, selectedId],
  )

  return (
    <main className="showcase-page">
      <section className="showcase-head" aria-labelledby="showcase-title">
        <Tag className="showcase-eyebrow">Simulation Showcase</Tag>
        <Title id="showcase-title" level={1}>
          选择已配置策略，连接仿真展示实时效果
        </Title>
        <Paragraph>
          这里优先承接方案配置页保存的策略名称。后续接入仿真连接后，可在同一页展示状态、
          事件流和关键指标。
        </Paragraph>
      </section>

      <section className="showcase-layout" aria-label="推演展示工作区">
        <Card className="showcase-panel" variant="borderless">
          <div className="showcase-panel__head">
            <div>
              <Text strong>已配置策略</Text>
              <Text>选择一个业务人员保存过的策略配置</Text>
            </div>
            <DashboardOutlined />
          </div>

          {configuredStrategies.length > 0 ? (
            <Select
              className="showcase-select"
              value={selectedStrategy?.id}
              onChange={setSelectedId}
              options={configuredStrategies.map((strategy) => ({
                value: strategy.id,
                label: strategy.configuredName,
              }))}
            />
          ) : (
            <Empty
              description="暂无已配置策略，请先在方案配置页保存业务偏好。"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>

        <Card className="showcase-detail" variant="borderless">
          {selectedStrategy ? (
            <>
              <div className="showcase-detail__title">
                <div>
                  <Text>当前策略配置</Text>
                  <Title level={2}>{selectedStrategy.configuredName}</Title>
                </div>
                <Tag color="success">已保存</Tag>
              </div>

              <div className="showcase-metrics">
                <div>
                  <Text>来源方案</Text>
                  <strong>{selectedStrategy.schemeName}</strong>
                </div>
                <div>
                  <Text>策略分支</Text>
                  <strong>{selectedStrategy.strategyName ?? '总体方案约束'}</strong>
                </div>
                <div>
                  <Text>想定</Text>
                  <strong>{selectedStrategy.scenarioName}</strong>
                </div>
              </div>

              <div className="showcase-summary">
                <Space>
                  <RadarChartOutlined />
                  <Text strong>{selectedStrategy.preferences.optimizationTarget}</Text>
                </Space>
                <Paragraph>{selectedStrategy.preferences.branchPreference}</Paragraph>
              </div>
            </>
          ) : (
            <div className="showcase-placeholder">
              <LinkOutlined />
              <Title level={2}>等待策略配置</Title>
              <Paragraph>保存后的策略名称会出现在这里，供后续仿真连接选择。</Paragraph>
            </div>
          )}
        </Card>
      </section>
    </main>
  )
}

export default SimulationShowcasePage
