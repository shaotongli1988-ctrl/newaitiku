function normalizeString(value) {
  return String(value || '').trim()
}

function normalizeNumber(value, fallback = 0) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : fallback
}

function normalizeMasteryRow(rowPayload) {
  const row = rowPayload && typeof rowPayload === 'object' ? rowPayload : {}
  return {
    studentUserId: normalizeString(row.studentUserId),
    subjectId: normalizeString(row.subjectId),
    accuracy: normalizeNumber(row.accuracy, 0),
    speed: normalizeNumber(row.speed, 0),
    frequency: normalizeNumber(row.frequency, 0),
    mastery: normalizeNumber(row.mastery, 0),
  }
}

function normalizeStudentRankingRow(rowPayload) {
  const row = rowPayload && typeof rowPayload === 'object' ? rowPayload : {}
  return {
    studentUserId: normalizeString(row.studentUserId),
    averageMastery: normalizeNumber(row.averageMastery, 0),
    subjectCount: normalizeNumber(row.subjectCount, 0),
    latestSubmittedAt: normalizeString(row.latestSubmittedAt),
  }
}

function normalizeLowActivityRow(rowPayload) {
  const row = rowPayload && typeof rowPayload === 'object' ? rowPayload : {}
  return {
    studentUserId: normalizeString(row.studentUserId),
    activityCount: normalizeNumber(row.activityCount, 0),
    latestSubmittedAt: normalizeString(row.latestSubmittedAt),
  }
}

export function createEmptyAnalyticsSummary() {
  return {
    timeRangeLabel: '全部时间',
    studentCount: 0,
    activeStudentCount: 0,
    inactiveStudentCount: 0,
    coverageRate: 0,
    questionCount: 0,
    averageAccuracy: 0,
    averageAnswerDurationSec: 0,
    masteredStudentCount: 0,
    atRiskStudentCount: 0,
    chapterRankings: [],
    weakKnowledgeTags: [],
    lowActivityStudents: [],
    mastery: [],
    studentRankings: [],
    aiReport: '',
  }
}

export function normalizeAnalyticsSummary(summaryPayload) {
  const payload = summaryPayload && typeof summaryPayload === 'object' ? summaryPayload : {}
  return {
    ...createEmptyAnalyticsSummary(),
    ...payload,
    chapterRankings: Array.isArray(payload.chapterRankings) ? payload.chapterRankings : [],
    weakKnowledgeTags: Array.isArray(payload.weakKnowledgeTags) ? payload.weakKnowledgeTags : [],
    lowActivityStudents: Array.isArray(payload.lowActivityStudents)
      ? payload.lowActivityStudents.map(normalizeLowActivityRow)
      : [],
    mastery: Array.isArray(payload.mastery)
      ? payload.mastery.map(normalizeMasteryRow)
      : [],
    studentRankings: Array.isArray(payload.studentRankings)
      ? payload.studentRankings.map(normalizeStudentRankingRow)
      : [],
  }
}
