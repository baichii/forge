import { BranchesOutlined } from '@ant-design/icons'
import { Layout } from 'antd'
import { Link, NavLink, Outlet } from 'react-router-dom'
import './WorkbenchShell.css'

const { Content, Footer, Header } = Layout

function WorkbenchShell() {
  return (
    <Layout className="workbench-shell">
      <Header className="workbench-header">
        <div className="workbench-header__inner">
          <Link className="workbench-brand" to="/">
            battle-planner
          </Link>
          <nav className="workbench-nav" aria-label="工作台导览">
            <NavLink to="/strategy">方案配置</NavLink>
            <Link to="/#strategy-iteration">策略迭代</Link>
            <NavLink to="/showcase">推演展示</NavLink>
          </nav>
        </div>
      </Header>

      <Content className="workbench-content">
        <Outlet />
      </Content>

      <Footer className="workbench-footer">
        <span>
          <BranchesOutlined /> battle_planner · 静态策略迭代工作台
        </span>
      </Footer>
    </Layout>
  )
}

export default WorkbenchShell
