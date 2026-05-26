import { ConfigProvider } from 'antd'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import WorkbenchShell from './layouts/WorkbenchShell'
import HomePage from './pages/HomePage'
import SimulationShowcasePage from './pages/SimulationShowcasePage'
import StrategyConfigPage from './pages/StrategyConfigPage'
import { antdTheme } from './styles/antdTheme'

function App() {
  return (
    <ConfigProvider theme={antdTheme}>
      <BrowserRouter>
        <Routes>
          <Route element={<WorkbenchShell />}>
            <Route index element={<HomePage />} />
            <Route path="strategy" element={<StrategyConfigPage />} />
            <Route path="showcase" element={<SimulationShowcasePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
