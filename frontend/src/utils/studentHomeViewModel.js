export function clampPercent(value) {
  const normalized = Number(value || 0)
  if (!Number.isFinite(normalized)) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

const DAILY_QUOTE_PREFIXES = [
  '心有热望',
  '脚下有路',
  '向难而行',
  '日拱一卒',
  '向上生长',
]

const DAILY_QUOTE_SUFFIXES = [
  '星河自明',
  '终见远方',
  '必有回响',
  '自有答案',
  '山海可越',
  '前路可期',
  '自成光芒',
  '可抵群峰',
  '终有收获',
  '定见山顶',
  '终会开花',
  '必有所得',
  '皆成伏笔',
  '皆有着落',
  '更近一程',
  '更胜昨日',
  '不负晨光',
  '不负此心',
  '梦想可及',
  '未来可追',
  '厚积薄发',
  '稳稳生长',
  '自会出众',
  '可穿风雨',
  '能越长坡',
  '足以破局',
  '必抵热爱',
  '终成底气',
  '终得明朗',
  '终可凯旋',
  '会被看见',
  '会有晴空',
  '会向上扬',
  '自能成峰',
  '自能发亮',
  '自能突围',
  '自能成章',
  '自有新章',
  '自有晴天',
  '自有朝阳',
  '自有回甘',
  '自有锋芒',
  '终能如愿',
  '终会抵达',
  '终会拔节',
  '终会登场',
  '可开新局',
  '可成习惯',
  '可见繁花',
  '可化春风',
  '可换成长',
  '可迎跃迁',
  '可聚星火',
  '可积千里',
  '可照前程',
  '可生万钧',
  '会长成树',
  '会筑成桥',
  '会写成诗',
  '会结成海',
  '会汇成河',
  '会织成锦',
  '会燃成炬',
  '会迎新晴',
  '会开满山',
  '会踏平川',
  '会映长空',
  '会鸣四方',
  '会到彼岸',
  '会成勋章',
  '会有回声',
  '会开新页',
  '会见曙光',
]

const DAILY_QUOTE_OVERRIDES = {
  81: '玉汝于成 功不唐捐',
}

export const DAILY_MOTIVATIONAL_QUOTES = Array.from({ length: 365 }, (_, index) => {
  const dayOfYear = index + 1
  if (DAILY_QUOTE_OVERRIDES[dayOfYear]) {
    return DAILY_QUOTE_OVERRIDES[dayOfYear]
  }
  const prefix = DAILY_QUOTE_PREFIXES[index % DAILY_QUOTE_PREFIXES.length]
  const suffix = DAILY_QUOTE_SUFFIXES[Math.floor(index / DAILY_QUOTE_PREFIXES.length)]
  return `${prefix}，${suffix}`
})

if (new Set(DAILY_MOTIVATIONAL_QUOTES).size !== DAILY_MOTIVATIONAL_QUOTES.length) {
  throw new Error('Daily motivational quotes must stay unique across 365 days.')
}

export function getDayOfYear(date = new Date()) {
  const normalizedDate = date instanceof Date ? date : new Date(date)
  if (Number.isNaN(normalizedDate.getTime())) {
    return 1
  }
  const year = normalizedDate.getFullYear()
  return Math.floor(
    (Date.UTC(year, normalizedDate.getMonth(), normalizedDate.getDate()) - Date.UTC(year, 0, 0)) / 86400000,
  )
}

export function resolveDailyMotivationalQuote(date = new Date()) {
  const dayOfYear = getDayOfYear(date)
  const quoteIndex = Math.max(0, (dayOfYear - 1) % DAILY_MOTIVATIONAL_QUOTES.length)
  return DAILY_MOTIVATIONAL_QUOTES[quoteIndex]
}

export function normalizeKnowledgeMastery(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  const normalized = numericValue > 1 ? numericValue : numericValue * 100
  return clampPercent(normalized)
}

export function buildReferenceMastery(subjectItem = {}, index = 0) {
  const label = `${subjectItem?.subjectCode || ''} ${subjectItem?.subjectName || ''}`.toUpperCase()
  if (label.includes('POLIT') || label.includes('政治')) {
    return 66
  }
  if (label.includes('ENGLISH') || label.includes('英语')) {
    return 61
  }
  if (label.includes('MATH') || label.includes('数学') || label.includes('高数')) {
    return 58
  }
  if (label.includes('CHINESE') || label.includes('语文')) {
    return 64
  }
  if (label.includes('COMPUTER') || label.includes('计算机')) {
    return 60
  }
  const fallbackScores = [62, 60, 59, 63, 57]
  return fallbackScores[index % fallbackScores.length]
}

export function derivePredictedScore({
  backendScore = 0,
  hasPersonalMastery = false,
  averageMastery = 0,
  averageAccuracy = 0,
  coveragePercent = 0,
} = {}) {
  const normalizedBackendScore = Number(backendScore || 0)
  if (Number.isFinite(normalizedBackendScore) && normalizedBackendScore > 0) {
    return Math.max(0, Math.min(300, Math.round(normalizedBackendScore)))
  }

  if (!hasPersonalMastery) {
    return 215
  }

  const derivedScore = 152
    + (Number(averageMastery || 0) * 0.78)
    + (Number(averageAccuracy || 0) * 0.3)
    + (Number(coveragePercent || 0) * 0.16)

  return Math.max(180, Math.min(300, Math.round(derivedScore)))
}

export function buildUrgentKnowledgeSuggestion({
  weakKnowledgeCandidates = [],
  referenceGroupLabel = '当前专业组',
} = {}) {
  const normalizedCandidates = Array.isArray(weakKnowledgeCandidates) ? weakKnowledgeCandidates : []
  const urgentTarget = normalizedCandidates.find((item) => Number(item?.mastery || 0) < 60)
  if (urgentTarget) {
    return {
      tone: 'risk',
      title: '最紧急补短板',
      message: `${urgentTarget.subjectName}：${urgentTarget.label} 掌握偏弱，建议优先复习并立即做 10 道同类强化题。`,
      detail: `当前掌握度 ${urgentTarget.mastery}% · ${urgentTarget.questionCount} 题关联 · 科目覆盖率 ${urgentTarget.subjectCoverage}%`,
      actionLabel: '立即补强',
      target: urgentTarget,
    }
  }

  const nextTarget = normalizedCandidates[0]
  if (nextTarget) {
    return {
      tone: 'steady',
      title: '下一步提分点',
      message: `${nextTarget.subjectName}：${nextTarget.label} 还可以继续拉高，建议趁热做一轮专项巩固。`,
      detail: `当前掌握度 ${nextTarget.mastery}% · 已进入相对稳定区，但仍有提升空间。`,
      actionLabel: '继续巩固',
      target: nextTarget,
    }
  }

  return {
    tone: 'empty',
    title: 'AI 助教待命中',
    message: '当前还没有足够的 L5 学情数据，先完成一轮练习，系统就会自动推送最紧急的补短建议。',
    detail: `默认按 ${referenceGroupLabel} 的参考曲线展示首屏结构。`,
    actionLabel: '去做任务',
    target: null,
  }
}

export function buildFocusedUrgentKnowledgeSuggestion({
  weakKnowledgeCandidates = [],
  currentSubjectCode = '',
  referenceGroupLabel = '当前专业组',
} = {}) {
  const normalizedSubjectCode = String(currentSubjectCode || '').trim()
  const normalizedCandidates = Array.isArray(weakKnowledgeCandidates) ? weakKnowledgeCandidates : []
  const focusedCandidates = normalizedSubjectCode
    ? normalizedCandidates.filter((item) => String(item?.subjectCode || '').trim() === normalizedSubjectCode)
    : normalizedCandidates

  return buildUrgentKnowledgeSuggestion({
    weakKnowledgeCandidates: focusedCandidates,
    referenceGroupLabel,
  })
}

function normalizeDailyTaskProgress(task = {}) {
  const completed = Math.max(0, Number(task?.completed || 0))
  const target = Math.max(0, Number(task?.target || 0))
  return {
    completed,
    target,
    percent: target > 0 ? clampPercent((completed / target) * 100) : 0,
  }
}

export function buildTodayExecutionRecommendation({
  checkInDone = false,
  streakDays = 0,
  nextDailyTask = null,
  urgentKnowledgeSuggestion = null,
  dailyCompletionPercent = 0,
  currentSubjectName = '当前科目',
} = {}) {
  const normalizedSubjectName = String(currentSubjectName || '').trim() || '当前科目'
  const normalizedSuggestion = urgentKnowledgeSuggestion && typeof urgentKnowledgeSuggestion === 'object'
    ? urgentKnowledgeSuggestion
    : {}
  const urgentTarget = normalizedSuggestion?.target && typeof normalizedSuggestion.target === 'object'
    ? normalizedSuggestion.target
    : null
  const urgentMastery = Number(urgentTarget?.mastery || 100)
  const normalizedDailyCompletionPercent = clampPercent(dailyCompletionPercent)
  const progress = normalizeDailyTaskProgress(nextDailyTask || {})

  if (!checkInDone) {
    return {
      kind: 'checkIn',
      title: '先完成今日打卡，再开始后面的练习',
      description: '打卡完成后，今日任务、补弱建议和段位积分会沿同一条执行线继续往下推进。',
      helper: Number(streakDays || 0) > 0 ? `已连续达成 ${Number(streakDays || 0)} 天` : '完成后可领取今日积分并拉起今天节奏',
      actionLabel: '先完成打卡',
      task: null,
      target: null,
    }
  }

  if (urgentTarget && urgentMastery < 45) {
    return {
      kind: 'weakness',
      title: `先补 ${urgentTarget.subjectName || normalizedSubjectName} 的「${urgentTarget.label || '薄弱点'}」`,
      description: normalizedSuggestion.message
        || `${urgentTarget.subjectName || normalizedSubjectName} 当前有明显薄弱点，优先补一轮，后面的段位分才更容易涨在真正决定升本结果的点上。`,
      helper: normalizedSuggestion.detail
        || `掌握度 ${clampPercent(urgentMastery)}% · 关联题量 ${Math.max(0, Number(urgentTarget.questionCount || 0))}`,
      actionLabel: String(normalizedSuggestion.actionLabel || '去补弱项').trim() || '去补弱项',
      task: null,
      target: urgentTarget,
    }
  }

  if (nextDailyTask && !nextDailyTask?.isDone) {
    return {
      kind: 'task',
      title: `先做${nextDailyTask.taskName || '今日任务'}`,
      description: String(nextDailyTask?.actionLabel || '').trim()
        ? `${String(nextDailyTask.actionLabel).trim()}，先把今天最该拿的分拿下。`
        : '先把今天最该拿的分拿下，再决定是否展开更多补弱动作。',
      helper: progress.target > 0
        ? `已完成 ${progress.completed}/${progress.target} · 今日任务进度 ${normalizedDailyCompletionPercent}%`
        : `今日任务进度 ${normalizedDailyCompletionPercent}%`,
      actionLabel: String(nextDailyTask?.actionLabel || '去完成').trim() || '去完成',
      task: nextDailyTask,
      target: null,
    }
  }

  if (urgentTarget) {
    return {
      kind: 'weakness',
      title: `今天主线已推进，顺手补一下「${urgentTarget.label || '薄弱点'}」`,
      description: normalizedSuggestion.message
        || `${urgentTarget.subjectName || normalizedSubjectName} 还有可以继续拉高的薄弱点，现在补一轮，通常更容易把今天的训练继续转成稳定段位分。`,
      helper: normalizedSuggestion.detail
        || `掌握度 ${clampPercent(urgentMastery)}% · 关联题量 ${Math.max(0, Number(urgentTarget.questionCount || 0))}`,
      actionLabel: String(normalizedSuggestion.actionLabel || '继续巩固').trim() || '继续巩固',
      task: null,
      target: urgentTarget,
    }
  }

  if (nextDailyTask) {
    return {
      kind: 'task',
      title: `今天主线已完成，继续巩固「${nextDailyTask.taskName || '今日任务'}」也可以`,
      description: '今天的基础动作已经跑通，现在更适合回看一次任务或转去刷题段位，把今天的正确输出继续放大。',
      helper: `今日任务进度 ${normalizedDailyCompletionPercent}%`,
      actionLabel: String(nextDailyTask?.actionLabel || '再次进入').trim() || '再次进入',
      task: nextDailyTask,
      target: null,
    }
  }

  return {
    kind: 'empty',
    title: `${normalizedSubjectName} 暂时没有更紧急的单项任务`,
    description: '可以直接进入刷题段位，或者先看知识诊断再决定下一步补强方向。',
    helper: `今日任务进度 ${normalizedDailyCompletionPercent}%`,
    actionLabel: '去刷题升本',
    task: null,
    target: null,
  }
}
