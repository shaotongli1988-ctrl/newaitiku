function toText(value) {
  return String(value || '').trim()
}

const TASKS_ERROR_STATE_META = Object.freeze({
  dashboard: {
    title: '今日任务暂时加载失败',
    fallbackMessage: '今日任务数据加载失败',
  },
  taskList: {
    title: '任务记录暂时加载失败',
    fallbackMessage: '任务流水加载失败',
  },
  graphSummary: {
    title: '弱项摘要加载失败',
    fallbackMessage: '弱项摘要加载失败',
  },
  weakPoint: {
    title: '弱项提醒暂时加载失败',
    fallbackMessage: '弱项摘要加载失败',
  },
})

const TASKS_STATUS_META = Object.freeze({
  FAILED: {
    tone: 'danger',
    label: '执行失败',
    actionLabelWithAction: '重试任务',
    actionLabelWithoutAction: '查看补救动作',
  },
  RUNNING: {
    tone: 'info',
    label: '进行中',
    actionLabelWithAction: '继续执行',
    actionLabelWithoutAction: '查看进度',
  },
  SUCCESS: {
    tone: 'success',
    label: '已完成',
    actionLabelWithAction: '再次进入',
    actionLabelWithoutAction: '回诊断总览',
  },
  DONE: {
    tone: 'success',
    label: '已完成',
    actionLabelWithAction: '再次进入',
    actionLabelWithoutAction: '回诊断总览',
  },
  COMPLETED: {
    tone: 'success',
    label: '已完成',
    actionLabelWithAction: '再次进入',
    actionLabelWithoutAction: '回诊断总览',
  },
  FINISHED: {
    tone: 'success',
    label: '已完成',
    actionLabelWithAction: '再次进入',
    actionLabelWithoutAction: '回诊断总览',
  },
})

export function buildTasksExecutionScopeNote(subjectName = '') {
  return `今日任务按全局学习节奏汇总展示；弱项提醒覆盖全部科目，点击后按对应科目进入补强。`
}

export function buildTaskOverviewCards({
  recentTaskCount = 0,
  runningCount = 0,
  failedCount = 0,
  completedCount = 0,
} = {}) {
  return [
    { label: '最近记录', value: Math.max(0, Number(recentTaskCount || 0)), helper: '基于当前可见任务记录' },
    { label: '最近进行中', value: Math.max(0, Number(runningCount || 0)), helper: '当前列表内仍在执行', tone: 'info' },
    { label: '最近失败', value: Math.max(0, Number(failedCount || 0)), helper: '优先恢复这部分任务', tone: 'danger' },
    { label: '最近完成', value: Math.max(0, Number(completedCount || 0)), helper: '当前列表内已完成记录', tone: 'success' },
  ]
}

export function buildTaskRecordHeading(failedCount = 0) {
  return Number(failedCount || 0) > 0 ? '待恢复与最近执行' : '最近执行记录'
}

export function buildTaskSummaryFootnote(recentCount = 0, totalCount = 0) {
  const normalizedRecentCount = Math.max(0, Number(recentCount || 0))
  const normalizedTotalCount = Math.max(0, Number(totalCount || 0))
  if (!normalizedRecentCount) {
    return '当前还没有可展示的全局任务记录。'
  }
  if (normalizedTotalCount > normalizedRecentCount) {
    return `以下摘要基于最近 ${normalizedRecentCount} 条全局记录，全量共 ${normalizedTotalCount} 条任务。`
  }
  return `以下摘要基于当前可见的 ${normalizedRecentCount} 条全局任务记录。`
}

export function buildDailyTaskScopeCopy() {
  return '这里汇总今天所有学习动作，不按当前科目拆分；弱项提醒会覆盖全部科目。'
}

export function buildTaskRecordScopeCopy() {
  return '最近执行记录沿用全局汇总口径，方便连续查看今天做过的所有动作。'
}

export function buildWeakPointScopeCopy(subjectName = '') {
  return '弱项提醒覆盖全部科目，点击后会按对应科目进入补弱。'
}

export function buildTasksErrorState(kind = '', errorMessage = '') {
  const meta = TASKS_ERROR_STATE_META[toText(kind)] || {
    title: '页面数据暂时加载失败',
    fallbackMessage: '页面数据加载失败',
  }
  return {
    title: meta.title,
    message: toText(errorMessage) || meta.fallbackMessage,
  }
}

export function buildTaskStatusMeta(status = '', hasExplicitAction = false) {
  const normalizedStatus = toText(status).toUpperCase()
  const meta = TASKS_STATUS_META[normalizedStatus]
  if (!meta) {
    return {
      tone: 'neutral',
      label: normalizedStatus || '待处理',
      actionLabel: hasExplicitAction ? '查看详情' : '查看诊断',
    }
  }
  return {
    tone: meta.tone,
    label: meta.label,
    actionLabel: hasExplicitAction ? meta.actionLabelWithAction : meta.actionLabelWithoutAction,
  }
}

export function normalizeTaskRecord(item = {}, index = 0) {
  const normalizedItem = item && typeof item === 'object' ? item : {}
  const hasExplicitAction = Boolean(
    toText(normalizedItem.actionPath) || toText(normalizedItem.taskKey),
  )
  const statusMeta = buildTaskStatusMeta(normalizedItem.status, hasExplicitAction)
  const progressValue = Math.max(0, Math.min(100, Number(normalizedItem.progress || 0)))

  return {
    ...normalizedItem,
    recordId: toText(normalizedItem.taskId || normalizedItem.id || `record-${index}`),
    title: toText(normalizedItem.taskName || normalizedItem.title || normalizedItem.type || `任务 ${index + 1}`),
    summary: toText(normalizedItem.actionLabel || normalizedItem.description || normalizedItem.type || '查看最新任务反馈'),
    helper: toText(normalizedItem.updateTime || normalizedItem.createTime || '-'),
    progressValue,
    statusLabel: statusMeta.label,
    statusTone: statusMeta.tone,
    actionLabel: statusMeta.actionLabel,
    hasExplicitAction,
  }
}
