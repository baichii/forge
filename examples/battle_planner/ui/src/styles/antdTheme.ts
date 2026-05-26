import type { ThemeConfig } from 'antd'

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: '#c96442',
    colorInfo: '#6f6a5f',
    colorSuccess: '#16823a',
    colorWarning: '#b7791f',
    colorError: '#b53333',
    colorTextBase: '#141413',
    colorTextSecondary: '#5e5d59',
    colorTextTertiary: '#87867f',
    colorBgBase: '#f5f4ed',
    colorBgLayout: '#f5f4ed',
    colorBgContainer: '#faf9f5',
    colorBgElevated: '#faf9f5',
    colorBorder: '#e8e6dc',
    colorBorderSecondary: '#f0eee6',
    colorFillTertiary: '#e8e6dc',
    borderRadius: 8,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 14,
    wireframe: false,
  },
  components: {
    Button: {
      borderRadius: 8,
      primaryColor: '#faf9f5',
      primaryShadow: 'none',
    },
    Card: {
      borderRadiusLG: 8,
      colorBgContainer: '#faf9f5',
    },
    Layout: {
      bodyBg: '#f5f4ed',
      headerBg: '#f5f4ed',
      footerBg: '#f5f4ed',
    },
    Tag: {
      borderRadiusSM: 999,
    },
  },
}
