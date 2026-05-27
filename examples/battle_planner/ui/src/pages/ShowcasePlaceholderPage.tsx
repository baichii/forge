import { DashboardOutlined } from '@ant-design/icons'
import { Card, Empty, Tag, Typography } from 'antd'
import './ShowcasePlaceholderPage.css'

const { Paragraph, Title } = Typography

function ShowcasePlaceholderPage() {
  return (
    <main className="showcase-placeholder-page">
      <section className="showcase-placeholder-head" aria-labelledby="showcase-placeholder-title">
        <Tag className="showcase-placeholder-eyebrow">Simulation View</Tag>
        <Title id="showcase-placeholder-title" level={1}>
          推演展示
        </Title>
        <Paragraph>
          这里预留给后续实时仿真展示界面。当前版本先不放置临时 UI，等视觉方案确定后再接入策略、
          仿真连接、态势视图和事件流。
        </Paragraph>
      </section>

      <Card className="showcase-placeholder-card" variant="borderless">
        <Empty
          description="推演展示页面待设计"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <DashboardOutlined />
        </Empty>
      </Card>
    </main>
  )
}

export default ShowcasePlaceholderPage
