import {
  CheckCircleFilled,
  FileTextOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import { Button, Form, Input, Radio, Select, Space, Tag, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import {
  buildBranchPreference,
  buildSchemePreference,
  schemeViews,
} from '../mocks/schemes'
import type {
  BusinessPreference,
  ConfiguredStrategy,
  SchemeView,
  StrategyBranchView,
} from '../types/strategy'
import { saveConfiguredStrategy } from '../utils/configuredStrategies'
import './StrategyConfigPage.css'

const { Paragraph, Text, Title } = Typography
const { TextArea } = Input

const SCHEME_CARD_ID = 'scheme-description'

const optimizationOptions = [
  '关键目标毁伤最大化',
  '我方平台生存优先',
  '武器消耗最小化',
  '压制并摧毁红方航母核心舰',
]

const riskOptions = [
  '稳健：避免连续高风险窗口',
  '均衡：接受短时高收益窗口',
  '激进：优先压缩完成时间',
]

const branchPreferenceOptions = [
  '保持当前单策略验证，不扩展额外分支。',
  '先空中突击压制，再由舰艇编队补充打击。',
  '保留武器余量，优先根据仿真报告做小步校准。',
]

function formatSavedTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

function buildDraftKey(scheme: SchemeView, selectedCardId: string) {
  return `${scheme.schemeId}:${selectedCardId}`
}

function getDefaultPreference(
  scheme: SchemeView,
  selectedBranch: StrategyBranchView | undefined,
) {
  return selectedBranch
    ? buildBranchPreference(selectedBranch)
    : buildSchemePreference(scheme)
}

function StrategyConfigPage() {
  const [form] = Form.useForm<BusinessPreference>()
  const [selectedSchemeId, setSelectedSchemeId] = useState(schemeViews[0].schemeId)
  const [selectedCardId, setSelectedCardId] = useState(SCHEME_CARD_ID)
  const [drafts, setDrafts] = useState<Record<string, BusinessPreference>>({})
  const [saveState, setSaveState] = useState('偏好草稿已就绪')

  const activeScheme =
    schemeViews.find((scheme) => scheme.schemeId === selectedSchemeId) ?? schemeViews[0]
  const selectedBranch =
    selectedCardId === SCHEME_CARD_ID
      ? undefined
      : activeScheme.branches.find((branch) => branch.strategyId === selectedCardId)
  const isSchemeSelected = selectedCardId === SCHEME_CARD_ID || !selectedBranch
  const draftKey = buildDraftKey(activeScheme, selectedCardId)

  const currentDraft = useMemo(
    () =>
      drafts[draftKey] ??
      getDefaultPreference(activeScheme, isSchemeSelected ? undefined : selectedBranch),
    [activeScheme, draftKey, drafts, isSchemeSelected, selectedBranch],
  )

  useEffect(() => {
    form.setFieldsValue(currentDraft)
  }, [currentDraft, form])

  function handleSchemeChange(nextSchemeId: string) {
    setSelectedSchemeId(nextSchemeId)
    setSelectedCardId(SCHEME_CARD_ID)
    setSaveState('已切换方案，等待保存')
  }

  function handleCardChange(nextCardId: string) {
    setSelectedCardId(nextCardId)
    setSaveState(nextCardId === SCHEME_CARD_ID ? '已选择方案描述' : '已选择策略分支')
  }

  function handleValuesChange(
    _changedValues: Partial<BusinessPreference>,
    values: BusinessPreference,
  ) {
    setDrafts((current) => ({
      ...current,
      [draftKey]: values,
    }))
    setSaveState('偏好已更新，等待保存')
  }

  function handleSave() {
    const savedAt = new Date().toISOString()
    const preferences = form.getFieldsValue() as BusinessPreference
    const configuredName =
      preferences.configuredName?.trim() ||
      (selectedBranch
        ? `${selectedBranch.name} · 业务偏好版`
        : `${activeScheme.name} · 总体约束版`)
    const payload: ConfiguredStrategy = {
      id: `${activeScheme.schemeId}-${selectedCardId}-${Date.now()}`,
      scope: isSchemeSelected ? 'scheme' : 'strategy',
      schemeId: activeScheme.schemeId,
      schemeName: activeScheme.name,
      scenarioName: activeScheme.scenarioName,
      strategyId: selectedBranch?.strategyId,
      strategyName: selectedBranch?.name,
      configuredName,
      preferences: {
        ...preferences,
        configuredName,
      },
      savedAt,
    }
    saveConfiguredStrategy(payload)
    setSaveState(`已保存：${configuredName} · ${formatSavedTime(savedAt)}`)
  }

  return (
    <main className="strategy-config-page">
      <section className="strategy-config-head" aria-labelledby="strategy-config-title">
        <div>
          <Tag className="strategy-config-eyebrow">Business Configuration</Tag>
          <Title id="strategy-config-title" level={1}>
            完全由业务驱动的约束配置
          </Title>
          <Paragraph className="strategy-config-lead">
            左侧选择上游平台规划好的推演方案与策略分支；右侧沉淀目标、约束和偏好，
            保存为后续推演可复用的策略配置。
          </Paragraph>
        </div>
        <div className="strategy-config-head__status">
          <CheckCircleFilled />
          <span>{saveState}</span>
        </div>
      </section>

      <section className="strategy-config-layout" aria-label="方案配置工作区">
        <aside className="strategy-config-side" aria-label="方案与策略">
          <div className="strategy-config-side__head">
            <Title level={2}>方案与策略</Title>
            <Text>来自上游平台方案库</Text>
          </div>

          <div className="strategy-config-picker">
            <Text strong>选择方案</Text>
            <Select
              value={selectedSchemeId}
              onChange={handleSchemeChange}
              options={schemeViews.map((scheme) => ({
                value: scheme.schemeId,
                label: `${scheme.name} / ${scheme.scenarioName}`,
              }))}
            />
          </div>

          <div className="strategy-config-list">
            <button
              className={
                isSchemeSelected
                  ? 'strategy-config-card strategy-config-card--active'
                  : 'strategy-config-card'
              }
              type="button"
              onClick={() => handleCardChange(SCHEME_CARD_ID)}
            >
              <span className="strategy-config-card__type">方案描述卡片</span>
              <strong>{activeScheme.name}</strong>
              <span>{activeScheme.objective}</span>
              <span className="strategy-config-card__meta">
                {activeScheme.scenarioName} · 蓝方 / 红方
              </span>
            </button>

            {activeScheme.branches.map((branch) => (
              <button
                className={
                  selectedBranch?.strategyId === branch.strategyId
                    ? 'strategy-config-card strategy-config-card--active'
                    : 'strategy-config-card'
                }
                key={branch.strategyId}
                type="button"
                onClick={() => handleCardChange(branch.strategyId)}
              >
                <span className="strategy-config-card__type">{branch.branchLabel}</span>
                <strong>{branch.name}</strong>
                <span>{branch.description}</span>
                <span className="strategy-config-card__meta">
                  {branch.tags.join(' · ')}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="strategy-config-editor" aria-live="polite">
          <div className="strategy-config-summary">
            <div>
              <Text className="strategy-config-summary__path">
                推演方案 /{' '}
                {isSchemeSelected
                  ? activeScheme.scenarioName
                  : `${selectedBranch?.branchLabel ?? '策略分支'} / ${selectedBranch?.name}`}
              </Text>
              <Title level={2}>
                {isSchemeSelected ? activeScheme.name : selectedBranch?.name}
              </Title>
              <Paragraph>
                {isSchemeSelected ? activeScheme.objective : selectedBranch?.description}
              </Paragraph>
            </div>
            <Space wrap className="strategy-config-tags">
              {(isSchemeSelected
                ? ['总体约束', '优化目标', '人工偏好']
                : selectedBranch?.tags ?? []
              ).map((tag) => (
                <Tag key={tag}>{tag}</Tag>
              ))}
            </Space>
          </div>

          <div className="strategy-config-facts" aria-label="业务信息摘要">
            <div>
              <Text>想定名称</Text>
              <strong>{activeScheme.scenarioName}</strong>
            </div>
            <div>
              <Text>作战方向</Text>
              <strong>蓝方 / 红方</strong>
            </div>
            <div>
              <Text>{isSchemeSelected ? '总体约束' : '平台打法'}</Text>
              <strong>
                {isSchemeSelected
                  ? `${activeScheme.constraints.length} 条`
                  : selectedBranch?.platformSummary}
              </strong>
            </div>
          </div>

          <div className="strategy-config-context">
            {(isSchemeSelected
              ? activeScheme.constraints
              : selectedBranch?.platformItems ?? []
            ).map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>

          <Form
            className="strategy-config-form"
            form={form}
            layout="vertical"
            onValuesChange={handleValuesChange}
          >
            <div className="strategy-config-form__grid">
              <Form.Item
                className="strategy-config-form__wide"
                label="配置名称"
                name="configuredName"
              >
                <Input placeholder="为本次保存的策略配置命名" />
              </Form.Item>

              <Form.Item
                label={isSchemeSelected ? '总体优化目标' : '分支目标'}
                name="optimizationTarget"
              >
                <Select
                  options={optimizationOptions.map((value) => ({
                    value,
                    label: value,
                  }))}
                />
              </Form.Item>

              <Form.Item
                label={isSchemeSelected ? '风险关注点' : '分支风险偏好'}
                name="riskFocus"
              >
                <Select
                  options={riskOptions.map((value) => ({
                    value,
                    label: value,
                  }))}
                />
              </Form.Item>

              <Form.Item
                className="strategy-config-form__wide"
                label={isSchemeSelected ? '总体约束' : '人工补充约束'}
                name="constraintNotes"
              >
                <TextArea autoSize={{ minRows: 3, maxRows: 6 }} />
              </Form.Item>

              <Form.Item
                className="strategy-config-form__timebox"
                label="时间窗偏好"
                name="timeWindowPreference"
              >
                <TextArea className="strategy-config-timebox" autoSize={false} />
              </Form.Item>

              <Form.Item label="偏好打法" name="branchPreference">
                <Radio.Group className="strategy-config-branch-options">
                  {branchPreferenceOptions.map((value) => (
                    <Radio key={value} value={value}>
                      {value}
                    </Radio>
                  ))}
                </Radio.Group>
              </Form.Item>

              <Form.Item
                className="strategy-config-form__wide"
                label="业务备注"
                name="notes"
              >
                <TextArea autoSize={{ minRows: 4, maxRows: 8 }} />
              </Form.Item>
            </div>
          </Form>

          <div className="strategy-config-editor__foot">
            <span>
              <FileTextOutlined /> 保存后生成“已配置策略”，供策略迭代与推演展示使用。
            </span>
            <Button
              icon={<SaveOutlined />}
              type="primary"
              size="large"
              onClick={handleSave}
            >
              保存业务偏好
            </Button>
          </div>
        </section>
      </section>

    </main>
  )
}

export default StrategyConfigPage
