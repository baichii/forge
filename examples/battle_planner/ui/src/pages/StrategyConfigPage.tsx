import {
  CheckCircleFilled,
  FileTextOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App as AntdApp,
  Button,
  Form,
  Input,
  Select,
  Spin,
  Tag,
  Typography,
} from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { battlePlannerClient } from '../api/battlePlannerClient'
import type {
  BranchHumanInput,
  PlanHumanInput,
  RiskStyle,
  TaskBranch,
  TaskContext,
  TaskContextCreateRequest,
  TaskPlan,
} from '../api/types'
import './StrategyConfigPage.css'

const { Paragraph, Text, Title } = Typography
const { TextArea } = Input

const PLAN_CARD_ID = 'plan-description'

type TaskContextPreference = {
  contextName: string
  optimizationTarget: string
  riskStyle: RiskStyle
  constraintNotes: string
  riskPoints: string
  notes: string
}

const riskOptions = [
  { label: '均衡', value: 'balanced' },
  { label: '激进', value: 'aggressive' },
  { label: '保守', value: 'conservative' },
]

const emptyPreference: TaskContextPreference = {
  contextName: '',
  optimizationTarget: '',
  riskStyle: 'balanced',
  constraintNotes: '',
  riskPoints: '',
  notes: '',
}

function formatSavedTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

function buildDraftKey(plan: TaskPlan, selectedCardId: string) {
  return `${plan.plan_id}:${selectedCardId}`
}

function buildBranchCardId(branch: TaskBranch) {
  return `branch-${branch.branch_id}`
}

function getSelectedBranch(plan: TaskPlan | undefined, selectedCardId: string) {
  if (!plan || selectedCardId === PLAN_CARD_ID) {
    return undefined
  }
  return plan.branches.find((branch) => buildBranchCardId(branch) === selectedCardId)
}

function getDefaultPreference(
  plan: TaskPlan | undefined,
  selectedBranch: TaskBranch | undefined,
): TaskContextPreference {
  if (!plan) {
    return emptyPreference
  }
  if (selectedBranch) {
    return {
      contextName: `${selectedBranch.name} · 业务偏好版`,
      optimizationTarget: selectedBranch.description,
      riskStyle: 'balanced',
      constraintNotes: getBranchItems(selectedBranch).join('\n'),
      riskPoints: '',
      notes: '',
    }
  }
  return {
    contextName: `${plan.name} · 总体约束版`,
    optimizationTarget: plan.objective,
    riskStyle: 'balanced',
    constraintNotes: plan.constraints.join('\n'),
    riskPoints: '',
    notes: '',
  }
}

function StrategyConfigPage() {
  const { message } = AntdApp.useApp()
  const [form] = Form.useForm<TaskContextPreference>()
  const [plans, setPlans] = useState<TaskPlan[]>([])
  const [selectedPlanId, setSelectedPlanId] = useState('')
  const [selectedCardId, setSelectedCardId] = useState(PLAN_CARD_ID)
  const [drafts, setDrafts] = useState<Record<string, TaskContextPreference>>({})
  const [saveState, setSaveState] = useState('正在读取任务方案')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [savedContext, setSavedContext] = useState<TaskContext | null>(null)

  useEffect(() => {
    let mounted = true
    battlePlannerClient
      .listPlans()
      .then((items) => {
        if (!mounted) {
          return
        }
        setPlans(items)
        setSelectedPlanId((current) => current || items[0]?.plan_id || '')
        setSaveState(items.length ? '偏好草稿已就绪' : '暂无可配置任务方案')
      })
      .catch((error: unknown) => {
        if (!mounted) {
          return
        }
        setLoadError(error instanceof Error ? error.message : '任务方案读取失败')
        setSaveState('任务方案读取失败')
      })
      .finally(() => {
        if (mounted) {
          setIsLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  const activePlan = plans.find((plan) => plan.plan_id === selectedPlanId) ?? plans[0]
  const selectedBranch = getSelectedBranch(activePlan, selectedCardId)
  const isPlanSelected = selectedCardId === PLAN_CARD_ID || !selectedBranch
  const draftKey = activePlan ? buildDraftKey(activePlan, selectedCardId) : ''

  const currentDraft = useMemo(
    () =>
      activePlan
        ? drafts[draftKey] ??
          getDefaultPreference(activePlan, isPlanSelected ? undefined : selectedBranch)
        : emptyPreference,
    [activePlan, draftKey, drafts, isPlanSelected, selectedBranch],
  )

  useEffect(() => {
    form.setFieldsValue(currentDraft)
  }, [currentDraft, form])

  function handlePlanChange(nextPlanId: string) {
    setSelectedPlanId(nextPlanId)
    setSelectedCardId(PLAN_CARD_ID)
    setSavedContext(null)
    setSaveState('已切换任务方案，等待保存')
  }

  function handleCardChange(nextCardId: string) {
    setSelectedCardId(nextCardId)
    setSavedContext(null)
    setSaveState(nextCardId === PLAN_CARD_ID ? '已选择方案总览' : '已选择方案分支')
  }

  function handleValuesChange(
    _changedValues: Partial<TaskContextPreference>,
    values: TaskContextPreference,
  ) {
    if (!activePlan) {
      return
    }
    setDrafts((current) => ({
      ...current,
      [draftKey]: values,
    }))
    setSavedContext(null)
    setSaveState('偏好已更新，等待保存')
  }

  async function handleSave() {
    if (!activePlan) {
      return
    }
    setIsSaving(true)
    try {
      const preferences = isPlanSelected
        ? await form.validateFields()
        : (form.getFieldsValue() as TaskContextPreference)
      const contextName = isPlanSelected
        ? preferences.contextName.trim()
        : buildBranchContextName(activePlan, selectedBranch)
      const request = buildContextRequest({
        plan: activePlan,
        selectedBranch,
        preferences: {
          ...preferences,
          contextName,
        },
      })
      const context = await battlePlannerClient.createContext(request)
      const savedAt = String(context.meta.created_at ?? new Date().toISOString())
      setSavedContext(context)
      setSaveState(`已保存 task-context：${context.name} · ${formatSavedTime(savedAt)}`)
      message.success('任务上下文已保存')
    } catch (error) {
      if (isFormValidationError(error)) {
        setSaveState('请补充必填信息')
        return
      }
      const errorMessage = error instanceof Error ? error.message : '任务上下文保存失败'
      setSaveState(errorMessage)
      message.error(errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <main className="strategy-config-page">
        <Spin tip="读取任务方案" />
      </main>
    )
  }

  if (loadError || !activePlan) {
    return (
      <main className="strategy-config-page">
        <Alert
          message="任务方案不可用"
          description={loadError || '暂无可配置任务方案'}
          type="warning"
          showIcon
        />
      </main>
    )
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
            左侧选择上游平台规划好的任务方案与分支；右侧沉淀目标、约束和偏好，
            保存为后续策略迭代可复用的 task-context。
          </Paragraph>
        </div>
        <div className="strategy-config-head__status">
          <CheckCircleFilled />
          <span>{saveState}</span>
        </div>
      </section>

      <section className="strategy-config-layout" aria-label="方案配置工作区">
        <aside className="strategy-config-side" aria-label="方案与分支">
          <div className="strategy-config-side__head">
            <Title level={2}>任务方案与分支</Title>
            <Text>来自上游平台方案库</Text>
          </div>

          <div className="strategy-config-picker">
            <Text strong>选择任务方案</Text>
            <Select
              value={activePlan.plan_id}
              onChange={handlePlanChange}
              options={plans.map((plan) => ({
                value: plan.plan_id,
                label: `${plan.name} / ${plan.scenario_name}`,
              }))}
            />
          </div>

          <div className="strategy-config-list">
            <div className="strategy-config-plan-tree">
              <button
                className={
                  isPlanSelected
                    ? 'strategy-config-card strategy-config-card--active'
                    : 'strategy-config-card'
                }
                type="button"
                onClick={() => handleCardChange(PLAN_CARD_ID)}
              >
                <span className="strategy-config-card__type">方案总览</span>
                <strong>{activePlan.name}</strong>
                <span>{activePlan.objective}</span>
                <span className="strategy-config-card__meta">
                  {activePlan.scenario_name} · {activePlan.side} / {activePlan.opponent_side}
                </span>
              </button>

              <div className="strategy-config-branch-list" aria-label="方案分支">
                {activePlan.branches.map((branch) => (
                  <button
                    className={
                      selectedBranch?.branch_id === branch.branch_id
                        ? 'strategy-config-card strategy-config-card--branch strategy-config-card--active'
                        : 'strategy-config-card strategy-config-card--branch'
                    }
                    key={branch.branch_id}
                    type="button"
                    onClick={() => handleCardChange(buildBranchCardId(branch))}
                  >
                    <span className="strategy-config-card__type">分支 {branch.branch_id}</span>
                    <strong>{branch.name}</strong>
                    <span>{branch.description}</span>
                    <span className="strategy-config-card__meta">
                      {getBranchSummary(branch)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <section className="strategy-config-editor" aria-live="polite">
          <div className="strategy-config-summary">
            <div>
              <Text className="strategy-config-summary__path">
                任务方案 /{' '}
                {isPlanSelected
                  ? activePlan.scenario_name
                  : `分支 ${selectedBranch?.branch_id ?? '-'} / ${selectedBranch?.name}`}
              </Text>
              <Title level={2}>
                {isPlanSelected ? activePlan.name : selectedBranch?.name}
              </Title>
              <Paragraph>
                {isPlanSelected ? activePlan.objective : selectedBranch?.description}
              </Paragraph>
            </div>
          </div>

          <div className="strategy-config-facts" aria-label="业务信息摘要">
            <div>
              <Text>想定名称</Text>
              <strong>{activePlan.scenario_name}</strong>
            </div>
            <div>
              <Text>我方</Text>
              <strong>{activePlan.side}</strong>
            </div>
            <div>
              <Text>敌方</Text>
              <strong>{activePlan.opponent_side}</strong>
            </div>
          </div>

          <div className="strategy-config-context">
            {(isPlanSelected
              ? activePlan.constraints
              : getBranchItems(selectedBranch)
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
              {isPlanSelected ? (
                <Form.Item
                  className="strategy-config-form__wide"
                  label="配置名称"
                  name="contextName"
                  rules={[
                    {
                      required: true,
                      whitespace: true,
                      message: '请输入配置名称',
                    },
                  ]}
                >
                  <Input placeholder="为本次保存的 task-context 命名" />
                </Form.Item>
              ) : null}

              <Form.Item
                className="strategy-config-form__wide"
                label={isPlanSelected ? '总体优化目标' : '分支目标'}
                name="optimizationTarget"
              >
                <TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
              </Form.Item>

              <Form.Item
                className="strategy-config-form__wide"
                label="风险偏好"
                name="riskStyle"
              >
                <Select options={riskOptions} />
              </Form.Item>

              <Form.Item
                className="strategy-config-form__wide"
                label={isPlanSelected ? '总体约束' : '人工补充约束'}
                name="constraintNotes"
              >
                <TextArea autoSize={{ minRows: 3, maxRows: 6 }} />
              </Form.Item>

              <Form.Item
                className="strategy-config-form__wide"
                label="风险点"
                name="riskPoints"
              >
                <TextArea autoSize={{ minRows: 3, maxRows: 6 }} />
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

          {savedContext ? (
            <div className="strategy-config-context-result">
              <Text>task-context-id</Text>
              <strong>{savedContext.context_id}</strong>
              <span>{savedContext.name}</span>
            </div>
          ) : null}

          <div className="strategy-config-editor__foot">
            <span>
              <FileTextOutlined /> 保存后生成 task-context，供策略迭代选择并创建 task-run。
            </span>
            <Button
              icon={<SaveOutlined />}
              type="primary"
              size="large"
              loading={isSaving}
              onClick={handleSave}
            >
              保存任务上下文
            </Button>
          </div>
        </section>
      </section>
    </main>
  )
}

function buildContextRequest({
  plan,
  selectedBranch,
  preferences,
}: {
  plan: TaskPlan
  selectedBranch: TaskBranch | undefined
  preferences: TaskContextPreference
}): TaskContextCreateRequest {
  const human = buildHumanInput(preferences)
  return {
    plan_id: plan.plan_id,
    name: preferences.contextName,
    plan_human: human,
    branch_humans: selectedBranch
      ? [
          {
            branch_id: selectedBranch.branch_id,
            human,
          },
        ]
      : [],
  }
}

function buildHumanInput(preferences: TaskContextPreference): PlanHumanInput & BranchHumanInput {
  return {
    goal: preferences.optimizationTarget,
    risk_style: preferences.riskStyle ?? 'balanced',
    constraints: splitLines(preferences.constraintNotes),
    risk_points: splitLines(preferences.riskPoints),
    notes: preferences.notes,
  }
}

function splitLines(value = '') {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function buildBranchContextName(plan: TaskPlan, selectedBranch: TaskBranch | undefined) {
  return selectedBranch
    ? `${plan.name} · ${selectedBranch.name}`
    : `${plan.name} · 分支配置`
}

function isFormValidationError(error: unknown) {
  return typeof error === 'object' && error !== null && 'errorFields' in error
}

function getBranchSummary(branch: TaskBranch | undefined) {
  return branch?.platform.summary ?? branch?.description ?? ''
}

function getBranchItems(branch: TaskBranch | undefined) {
  return branch?.platform.items ?? []
}

export default StrategyConfigPage
