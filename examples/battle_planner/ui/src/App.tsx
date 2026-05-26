import { ConfigProvider } from 'antd'
import HomePage from './pages/HomePage'
import { antdTheme } from './styles/antdTheme'

function App() {
  return (
    <ConfigProvider theme={antdTheme}>
      <HomePage />
    </ConfigProvider>
  )
}

export default App
