import { DashboardOutlined } from '@ant-design/icons'
import { Card, Empty, Tag, Typography } from 'antd'
import './ShowcasePlaceholderPage.css'

const { Paragraph, Title } = Typography

function ShowcasePlaceholderPage() {
  return (
    <main className="showcase-placeholder-page">
      <section className="showcase-placeholder-head" aria-labelledby="showcase-placeholder-title">
        <Tag className="showcase-placeholder-eyebrow">推演展示</Tag>
        <Title id="showcase-placeholder-title" level={1}>
          推演展示
        </Title>
        <Paragraph>
          选择历史推演记录和策略轮次，查看态势变化、事件流、关键指标和执行要点。
        </Paragraph>
      </section>

      <Card className="showcase-placeholder-card" variant="borderless">
        <Empty
          description="请从导航进入推演展示工作区"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <DashboardOutlined />
        </Empty>
      </Card>
    </main>
  )
}

export default ShowcasePlaceholderPage
