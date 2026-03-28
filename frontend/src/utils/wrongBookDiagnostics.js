export function buildWrongBookDiagnosticBoard({
  questionInsights = [],
  currentSubject = {},
  effectiveSubjectCode = '',
  nowMs = Date.now(),
} = {}) {
  const recentWindow = 72 * 60 * 60 * 1000
  const recentNewWrongCount = (Array.isArray(questionInsights) ? questionInsights : []).filter((item) => {
    if (String(item?.subjectCode || '').trim() !== String(effectiveSubjectCode || '').trim()) {
      return false
    }
    const submittedAt = Date.parse(String(item?.submittedAt || '').trim())
    return Number.isFinite(submittedAt) && nowMs - submittedAt >= 0 && nowMs - submittedAt <= recentWindow
  }).length

  return {
    knowledgeCoverageRate: Math.round(Number(currentSubject?.knowledgeCoverageRate || 0) * 100),
    practicedPointCount: Number(currentSubject?.practicedPointCount || 0),
    totalPointCount: Number(currentSubject?.totalPointCount || 0),
    recentNewWrongCount,
    errorCoverageRate: Math.round(Number(currentSubject?.errorCoverageRate || 0) * 100),
    wrongCount: (Array.isArray(questionInsights) ? questionInsights : [])
      .filter((item) => String(item?.subjectCode || '').trim() === String(effectiveSubjectCode || '').trim()).length,
    hotspots: Array.isArray(currentSubject?.topChapters) ? currentSubject.topChapters.slice(0, 3) : [],
  }
}

export function buildWrongBookBreadcrumbTrail(semanticTrail = [], chapterLabel = '', pointLabel = '') {
  const normalizedTrail = Array.isArray(semanticTrail)
    ? semanticTrail.filter((item) => {
        const level = Number(item?.level || 0)
        return level >= 3 && level <= 5
      })
    : []
  if (normalizedTrail.length) {
    return normalizedTrail
  }
  return [
    chapterLabel ? { level: 4, levelLabel: 'L4 章节', label: chapterLabel } : null,
    pointLabel ? { level: 5, levelLabel: 'L5 原子知识点', label: pointLabel } : null,
  ].filter(Boolean)
}

export function buildWrongBookAiTutorPlan({
  knowledgeId = '',
  pointCode = '',
  pointName = '',
  chapterCode = '',
  chapterLabel = '',
  errorInducerLabel = '',
  reviewStatusKey = '',
  showBenchmarkRiskBadge = false,
  isOverdue72h = false,
  wrongCount = 0,
  repairSuggestions = [],
  chapterSuggestions = [],
} = {}) {
  const repairMatch = (Array.isArray(repairSuggestions) ? repairSuggestions : []).find((item) =>
    String(item?.knowledgeId || '').trim() === String(knowledgeId || '').trim()
    || String(item?.pointCode || '').trim() === String(pointCode || '').trim()
    || String(item?.pointName || '').trim() === String(pointName || '').trim(),
  )
  const chapterMatch = (Array.isArray(chapterSuggestions) ? chapterSuggestions : []).find((item) =>
    String(item?.chapterCode || '').trim() === String(chapterCode || '').trim()
    || String(item?.chapterName || '').trim() === String(chapterLabel || '').trim(),
  )
  const chapterFocus = chapterMatch?.chapterName || chapterLabel || chapterCode || '当前章节'
  const chapterDirective = chapterMatch?.suggestion
    || (chapterMatch?.dominantType === 'CALCULATION' ? '加强公式记忆' : '加强理论理解')
    || (errorInducerLabel === '计算题' ? '加强公式记忆' : '加强理论理解')

  let priorityLabel = '持续巩固'
  if (isOverdue72h) {
    priorityLabel = '72h 预警'
  } else if (showBenchmarkRiskBadge) {
    priorityLabel = '重灾区加急'
  } else if (reviewStatusKey === 'fragile') {
    priorityLabel = '优先修复'
  }

  return {
    priorityLabel,
    diagnosisTitle: repairMatch
      ? '底层逻辑错误'
      : errorInducerLabel === '计算题'
        ? '计算链路断点'
        : '概念理解偏差',
    recommendation: repairMatch?.message
      || `当前错因以${errorInducerLabel === '计算题' ? '运算与公式调用' : '概念辨析与理论理解'}为主，建议先回看错因再进入章节强化。`,
    chapterAction: `回到 L4「${chapterFocus}」，${chapterDirective}。`,
    actionLabel: isOverdue72h
      ? '今天先回顾原题，再补 2 道同类题。'
      : showBenchmarkRiskBadge
        ? '优先拉齐同组均值，先做弱项强化。'
        : wrongCount >= 3 || reviewStatusKey === 'fragile'
          ? '先看解析并口述思路，再做章节巩固。'
          : '保持间隔复习，避免再次回落。',
      }
}

export function resolveWrongBookPracticeSuggestionCount(practiceSuggestion = {}) {
  return Math.max(0, Number(practiceSuggestion?.questionCount || 0))
}

export function computeWrongBookPriorityAlertCount({
  benchmarkAlertRows = [],
  reviewWarnings = [],
  repairSuggestions = [],
} = {}) {
  return (
    (Array.isArray(benchmarkAlertRows) ? benchmarkAlertRows.length : 0)
    + (Array.isArray(reviewWarnings) ? reviewWarnings.length : 0)
    + (Array.isArray(repairSuggestions) ? repairSuggestions.length : 0)
  )
}
