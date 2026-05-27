import {
  ArrowRightOutlined,
  CheckCircleFilled,
  DashboardOutlined,
  HistoryOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { Card, Tag, Typography } from 'antd'
import { Link } from 'react-router-dom'
import './HomePage.css'

const { Paragraph, Text, Title } = Typography

const entryCards = [
  {
    key: 'configure',
    anchorId: 'scheme-configuration',
    href: '/strategy',
    icon: <SettingOutlined />,
    index: '01',
    title: '方案配置',
    description: '选择业务方案，查看方案描述与策略分支，配置总体约束、优化目标和人工偏好。',
  },
  {
    key: 'iteration',
    anchorId: 'strategy-iteration',
    href: '/iteration',
    icon: <HistoryOutlined />,
    index: '02',
    title: '策略迭代',
    description: '选择已配置策略和历史 session，查看多轮策略调整、指标变化和总结摘要。',
  },
  {
    key: 'showcase',
    anchorId: 'simulation-showcase',
    href: '/showcase',
    icon: <DashboardOutlined />,
    index: '03',
    title: '推演展示',
    description: '预留实时推演展示入口，待界面方案确定后承接仿真连接、态势视图和事件流。',
  },
]

function HomePage() {
  return (
    <main className="home-main">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero__copy">
          <Tag className="home-eyebrow">Strategy · Agent · Simulation</Tag>
          <Title id="home-title" className="home-title">
            把既定策略
            <br />
            转成智能体执行计划。
          </Title>
          <Paragraph className="home-lead">
            基于上游平台规划好的推演方案、分支方案和策略，自动生成智能体
            的执行时间窗、参与单位、目标与武器数量，并用仿真报告持续校准执行计划。
          </Paragraph>
        </div>

        <Card className="home-preview" variant="borderless">
          <div className="home-preview__head">
            <div>
              <Text strong>静态回放视图</Text>
              <Text className="home-preview__meta">方案配置 / 策略迭代 / 推演展示</Text>
            </div>
            <Tag color="success" icon={<CheckCircleFilled />}>
              可演示
            </Tag>
          </div>
          <div className="home-preview__body">
            <div className="home-preview__steps" aria-label="策略迭代阶段">
              <div className="home-step home-step--active">
                <Text strong>方案偏好</Text>
                <Text type="secondary">约束 · 目标 · 风险</Text>
              </div>
              <div className="home-step">
                <Text strong>策略推演</Text>
                <Text type="secondary">score · 毁伤 · 消耗</Text>
              </div>
              <div className="home-step">
                <Text strong>轮次摘要</Text>
                <Text type="secondary">summary · advice</Text>
              </div>
              <div className="home-step">
                <Text strong>推演展示</Text>
                <Text type="secondary">status · event · metric</Text>
              </div>
            </div>
            <div className="home-map" aria-hidden="true">
              <span className="home-map__route" />
              <span className="home-map__unit home-map__unit--blue" />
              <span className="home-map__unit home-map__unit--red" />
            </div>
          </div>
        </Card>
      </section>

      <section className="home-entries" aria-labelledby="entries-title">
        <div className="home-section-head">
          <Title id="entries-title" level={2}>
            从方案到推演
          </Title>
          <Paragraph>
            先沉淀业务偏好，再观察策略迭代证据，最后连接仿真展示实时效果。
          </Paragraph>
        </div>

        <div className="home-entry-grid">
          {entryCards.map((item) => {
            const content = (
              <Card className="home-entry__card" variant="borderless">
                <div>
                  <div className="home-entry__topline">
                    <span className="home-entry__index">{item.index}</span>
                    <span className="home-entry__icon">{item.icon}</span>
                  </div>
                  <Title level={3}>{item.title}</Title>
                  <Paragraph>{item.description}</Paragraph>
                </div>
                <div className="home-entry__foot">
                  <span>打开</span>
                  <ArrowRightOutlined />
                </div>
              </Card>
            )

            if (item.href.startsWith('/#')) {
              return (
                <a
                  id={item.anchorId}
                  className="home-entry"
                  href={item.href}
                  key={item.key}
                >
                  {content}
                </a>
              )
            }

            return (
              <Link
                id={item.anchorId}
                className="home-entry"
                key={item.key}
                to={item.href}
              >
                {content}
              </Link>
            )
          })}
        </div>
      </section>
    </main>
  )
}

export default HomePage
