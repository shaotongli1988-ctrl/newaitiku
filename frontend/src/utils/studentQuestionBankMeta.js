import { parseExtJson } from './question'

function toText(value) {
  return String(value || '').trim()
}

function toObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
}

export function formatQuestionBankDateTime(value) {
  const normalized = toText(value)
  if (!normalized) {
    return '-'
  }
  return normalized.replace('T', ' ').replace('Z', '')
}

export function buildPersonalBankQuestionMeta(row, { knowledgeSemanticMap = {} } = {}) {
  const extJson = parseExtJson(row?.extJson)
  const studentState = toObject(extJson?.studentState)
  const personalBankState = toObject(studentState?.personalBank)
  const wrongBookState = toObject(studentState?.wrongBook)
  const rowKnowledgeId = toText(row?.knowledgeId)
  const semantic = knowledgeSemanticMap[rowKnowledgeId] || {}
  const semanticTrail = Array.isArray(semantic?.semanticTrail) ? semantic.semanticTrail : []
  const level3Node = semanticTrail.find((item) => Number(item?.level || 0) === 3) || {}
  const level4Node = semanticTrail.find((item) => Number(item?.level || 0) === 4) || {}
  const level5Node = semanticTrail.find((item) => Number(item?.level || 0) === 5) || {}
  const sourceType = toText(personalBankState?.sourceType).toUpperCase()
  const sourceLabel = toText(personalBankState?.sourceLabel)
  const collectedAt = formatQuestionBankDateTime(personalBankState?.collectedAt)
  const archivedAt = formatQuestionBankDateTime(wrongBookState?.archivedAt)
  const restoredAt = formatQuestionBankDateTime(wrongBookState?.restoredAt)
  const reviewedAt = formatQuestionBankDateTime(wrongBookState?.reviewedAt)
  const isCollected = Boolean(personalBankState?.isCollected)
  const isArchived = Boolean(wrongBookState?.isArchived)
    || sourceType === 'HARVESTED_ARCHIVE'
    || sourceLabel === '已斩获归档'
  const stateLabels = []
  if (isCollected) {
    stateLabels.push('已进入沉淀题库')
  }
  if (isArchived) {
    stateLabels.push('已斩获归档')
  }
  if (restoredAt !== '-') {
    stateLabels.push('已恢复到错题中心')
  }
  if (reviewedAt !== '-') {
    stateLabels.push('已有复习记录')
  }

  return {
    knowledgeId: rowKnowledgeId,
    subjectCode: toText(extJson?.subjectCode),
    subjectId: toText(extJson?.subjectId) || '-',
    chapter: toText(extJson?.chapter) || '-',
    chapterCode: toText(extJson?.chapter_code),
    pointCode: toText(extJson?.point_code),
    pointLabel: toText(level5Node?.label),
    analysis: toText(extJson?.analysis),
    semanticPath: toText(semantic?.fullPathLabel),
    currentLevelLabel: toText(semantic?.levelLabel),
    semanticTrailIds: semanticTrail.map((item) => toText(item?.id)).filter(Boolean),
    semanticTrailLabels: semanticTrail.map((item) => toText(item?.label)).filter(Boolean),
    level3Id: toText(level3Node?.id),
    level3Label: toText(level3Node?.label),
    chapterId: toText(level4Node?.id),
    chapterLabel: toText(level4Node?.label || extJson?.chapter),
    sourceType,
    sourceLabel: sourceLabel || (isArchived ? '已斩获归档' : isCollected ? '已收藏' : ''),
    collectedAt,
    archivedAt,
    restoredAt,
    reviewedAt,
    isCollected,
    isArchived,
    reviewCount: Number(wrongBookState?.reviewCount || 0),
    lastReasonLabel: toText(wrongBookState?.lastReasonLabel),
    stateLabels,
    reasons: Array.isArray(wrongBookState?.reasonStats)
      ? wrongBookState.reasonStats.map((item) => toText(item?.reasonLabel)).filter(Boolean)
      : [],
  }
}

export function buildPersonalBankSearchText(row, meta) {
  return [
    row?.stem,
    row?.answer,
    meta?.analysis,
    meta?.semanticPath,
    meta?.level3Label,
    meta?.chapter,
    meta?.chapterCode,
    meta?.chapterLabel,
    meta?.pointCode,
    meta?.pointLabel,
    meta?.sourceLabel,
    ...(Array.isArray(meta?.reasons) ? meta.reasons : []),
  ]
    .map((item) => toText(item).toLowerCase())
    .filter(Boolean)
    .join(' ')
}

export function buildWrongBookQuestionMeta(
  row,
  {
    knowledgeSemanticMap = {},
    insightMap = {},
    similarQuestionsMap = {},
    currentRepairSuggestions = [],
    currentChapterInducerSuggestions = [],
    buildWrongBookBreadcrumbTrail,
    buildWrongBookAiTutorPlan,
  } = {},
) {
  const extJson = parseExtJson(row?.extJson)
  const studentState = extJson?.studentState && typeof extJson.studentState === 'object' ? extJson.studentState : {}
  const studentRecord = extJson?.studentRecord && typeof extJson.studentRecord === 'object' ? extJson.studentRecord : {}
  const recordExtJson = parseExtJson(studentRecord?.extJson)
  const chapterPractice = studentState?.chapterPractice && typeof studentState.chapterPractice === 'object'
    ? studentState.chapterPractice
    : (recordExtJson?.chapterPractice && typeof recordExtJson.chapterPractice === 'object' ? recordExtJson.chapterPractice : {})
  const wrongBookState = studentState?.wrongBook && typeof studentState.wrongBook === 'object'
    ? studentState.wrongBook
    : (recordExtJson?.wrongBook && typeof recordExtJson.wrongBook === 'object' ? recordExtJson.wrongBook : {})
  const rowKnowledgeId = toText(row?.knowledgeId)
  const semantic = knowledgeSemanticMap[rowKnowledgeId] || {}
  const insight = insightMap[toText(row?.id)] || {}
  const semanticTrail = Array.isArray(semantic?.semanticTrail) ? semantic.semanticTrail : []
  const semanticTagLine = semanticTrail.map((item) => `${toText(item.levelLabel)} ${toText(item.label)}`.trim()).filter(Boolean).join(' / ')
  const chapterNode = semanticTrail.find((item) => Number(item.level || 0) === 4) || {}
  const pointNode = semanticTrail.find((item) => Number(item.level || 0) === 5) || semanticTrail[semanticTrail.length - 1] || {}
  const chapterLabel = toText(chapterNode.label || extJson?.chapter || insight?.chapterName)
  const pointLabel = toText(pointNode.label || insight?.pointName || rowKnowledgeId)
  const jointGroupAccuracyGap = Number(insight?.jointGroupAccuracyGap || 0)
  const benchmarkStatusText = toText(insight?.benchmarkStatusText)
  const benchmarkTagType = toText(insight?.benchmarkTagType)
  const benchmarkRiskBadgeText = toText(insight?.benchmarkRiskBadgeText)
  const showBenchmarkRiskBadge = Boolean(insight?.showBenchmarkRiskBadge)
  const reviewStatusLabel = toText(insight?.reviewStatusLabel || '生疏') || '生疏'
  const reviewStatusKey = toText(insight?.reviewStatusKey || 'fragile') || 'fragile'
  const breadcrumbTrail = typeof buildWrongBookBreadcrumbTrail === 'function'
    ? buildWrongBookBreadcrumbTrail(semanticTrail, chapterLabel, pointLabel)
    : []

  return {
    knowledgeId: rowKnowledgeId,
    chapter: toText(extJson?.chapter) || toText(insight?.chapterName) || '-',
    chapterCode: toText(extJson?.chapter_code) || toText(insight?.chapterCode),
    pointCode: toText(extJson?.point_code) || toText(insight?.pointCode),
    pointName: toText(insight?.pointName) || rowKnowledgeId || '-',
    analysis: toText(extJson?.analysis) || '-',
    semanticPath: toText(semantic?.fullPathLabel),
    semanticTrail,
    semanticTagLine,
    currentLevelLabel: toText(semantic?.levelLabel),
    chapterLabel: chapterLabel || '-',
    pointLabel: pointLabel || toText(insight?.pointName) || '-',
    chapterPointPath: [chapterLabel, pointLabel].filter(Boolean).join(' > ') || '-',
    mastery: Number(insight?.mastery || 0),
    masteryScore: Number(insight?.masteryScore || 0),
    jointGroupAverageAccuracy: Number(insight?.jointGroupAverageAccuracy || 0),
    jointGroupAccuracyGap,
    benchmarkStatusText:
      benchmarkStatusText || (
        jointGroupAccuracyGap >= 0.3
          ? '明显落后同组，需立刻补齐'
          : jointGroupAccuracyGap >= 0.1
            ? '略落后同组，建议优先回看'
            : jointGroupAccuracyGap <= -0.1
              ? '已超越同组'
              : '接近同组均值'
      ),
    benchmarkTagType:
      benchmarkTagType || (
        jointGroupAccuracyGap >= 0.3
          ? 'danger'
          : jointGroupAccuracyGap >= 0.1
            ? 'warning'
            : jointGroupAccuracyGap <= -0.1
              ? 'success'
              : 'info'
      ),
    benchmarkRiskBadgeText: benchmarkRiskBadgeText || (jointGroupAccuracyGap >= 0.3 ? '同组高风险' : ''),
    showBenchmarkRiskBadge: showBenchmarkRiskBadge || jointGroupAccuracyGap >= 0.3,
    wrongCount: Number(insight?.wrongCount || 0),
    reviewStatusLabel,
    reviewStatusKey,
    reviewCount: Number(insight?.reviewCount || wrongBookState?.reviewCount || 0),
    reviewAccuracyRate: Number(insight?.reviewAccuracyRate || 0),
    postWrongAttemptCount: Number(insight?.postWrongAttemptCount || wrongBookState?.postWrongAttemptCount || 0),
    postWrongCorrectCount: Number(insight?.postWrongCorrectCount || wrongBookState?.postWrongCorrectCount || 0),
    errorInducerLabel: toText(insight?.errorInducerLabel || '-') || '-',
    lastReasonLabel: toText(wrongBookState?.lastReasonLabel),
    lastAnswer: toText(chapterPractice?.lastAnswer || chapterPractice?.normalizedAnswer),
    submitCount: Number(chapterPractice?.submitCount || 0),
    correctCount: Number(chapterPractice?.correctCount || 0),
    answerDurationSec: Number(chapterPractice?.answerDurationSec || 0),
    isOverdue72h: Boolean(insight?.isOverdue72h),
    submittedAt: formatQuestionBankDateTime(insight?.submittedAt),
    reviewedAt: formatQuestionBankDateTime(insight?.reviewedAt),
    overdueHours: Number(insight?.overdueHours || 0),
    pendingRepair: Boolean(insight?.isPendingRepair),
    breadcrumbTrail,
    aiTutorPlan: typeof buildWrongBookAiTutorPlan === 'function'
      ? buildWrongBookAiTutorPlan({
          knowledgeId: rowKnowledgeId,
          pointCode: toText(extJson?.point_code) || toText(insight?.pointCode),
          pointName: toText(insight?.pointName) || rowKnowledgeId || '-',
          chapterCode: toText(extJson?.chapter_code) || toText(insight?.chapterCode),
          chapterLabel: chapterLabel || '-',
          errorInducerLabel: toText(insight?.errorInducerLabel || '-') || '-',
          reviewStatusKey,
          showBenchmarkRiskBadge: showBenchmarkRiskBadge || jointGroupAccuracyGap >= 0.3,
          isOverdue72h: Boolean(insight?.isOverdue72h),
          wrongCount: Number(insight?.wrongCount || 0),
          repairSuggestions: currentRepairSuggestions,
          chapterSuggestions: currentChapterInducerSuggestions,
        })
      : {},
    similarQuestions: Array.isArray(similarQuestionsMap[toText(row?.id)])
      ? similarQuestionsMap[toText(row?.id)]
      : [],
  }
}
