import {
  clearPracticePathQuery,
  clearPracticeTransientFocusQuery,
  sanitizePracticeQuery,
} from './practiceScope.js'

export const STUDENT_SUBJECT_SYNC_ROUTE_PATHS = new Set([
  '/student/home',
  '/student/practice/chapter',
  '/student/practice/free',
  '/student/practice/mock',
  '/student/practice/tasks',
  '/student/points',
  '/student/analysis',
  '/student/analysis/overview',
  '/student/analysis/tasks',
  '/student/analysis/points',
  '/student/question-bank/repair',
  '/student/question-bank/archive',
])

function toText(value) {
  return String(Array.isArray(value) ? value[0] : value || '').trim()
}

export function resolveStudentSubjectCode(subjectOptions = [], ...candidateSubjectCodes) {
  const availableSubjectCodes = new Set(
    (Array.isArray(subjectOptions) ? subjectOptions : [])
      .map((item) => toText(item?.subjectCode))
      .filter(Boolean),
  )

  for (const candidateSubjectCode of candidateSubjectCodes.flat()) {
    const normalizedCandidateSubjectCode = toText(candidateSubjectCode)
    if (normalizedCandidateSubjectCode && availableSubjectCodes.has(normalizedCandidateSubjectCode)) {
      return normalizedCandidateSubjectCode
    }
  }

  return toText(subjectOptions?.[0]?.subjectCode)
}

export function normalizeStudentSubjectOptions(payloadOrRows) {
  const sourceRows = Array.isArray(payloadOrRows)
    ? payloadOrRows
    : Array.isArray(payloadOrRows?.coreSubjects)
      ? payloadOrRows.coreSubjects
      : []

  const seen = new Set()

  return sourceRows
    .map((item) => {
      const subjectCode = toText(item?.subjectCode)
      if (!subjectCode || seen.has(subjectCode)) {
        return null
      }
      seen.add(subjectCode)
      return {
        subjectCode,
        subjectId: toText(item?.subjectId),
        subjectName: toText(item?.subjectName || item?.subjectCode) || subjectCode,
        subjectType: toText(item?.subjectType),
        answered: Number(item?.progress?.answered ?? item?.answered ?? 0),
        total: Number(item?.progress?.total ?? item?.total ?? 0),
        accuracy: Number(item?.progress?.accuracy ?? item?.accuracy ?? 0),
      }
    })
    .filter(Boolean)
}

export function shouldSyncStudentSubjectRoute(path) {
  return STUDENT_SUBJECT_SYNC_ROUTE_PATHS.has(String(path || '').trim())
}

function sanitizeRouteQuery(query = {}) {
  const nextQuery = { ...(query || {}) }
  Object.keys(nextQuery).forEach((key) => {
    const value = nextQuery[key]
    if (value === undefined || value === null || toText(value) === '') {
      delete nextQuery[key]
    }
  })
  return nextQuery
}

function clearStudentKnowledgeFocusQuery(query = {}) {
  const nextQuery = { ...(query || {}) }
  delete nextQuery.knowledgePathNodeId
  delete nextQuery.knowledgeId
  delete nextQuery.chapterCode
  delete nextQuery.chapterName
  delete nextQuery.pointCode
  delete nextQuery.pointName
  delete nextQuery.pathLabel
  return nextQuery
}

export function buildStudentRouteLocationForSubject(route, subjectCode, subjectId = '') {
  const path = String(route?.path || '').trim()
  const normalizedSubjectCode = toText(subjectCode)
  const normalizedSubjectId = toText(subjectId)
  const rawQuery = { ...(route?.query || {}) }

  if (!normalizedSubjectCode) {
    return {
      path,
      query: sanitizeRouteQuery(rawQuery),
    }
  }

  if (path.startsWith('/student/practice')) {
    let nextQuery = {
      ...rawQuery,
      subjectCode: normalizedSubjectCode,
    }
    nextQuery = clearPracticePathQuery(nextQuery)
    nextQuery = clearPracticeTransientFocusQuery(nextQuery)
    if (path === '/student/practice/mock') {
      delete nextQuery.paperId
      delete nextQuery.sessionId
    }
    return {
      path,
      query: sanitizePracticeQuery(nextQuery),
    }
  }

  if (path.startsWith('/student/analysis')) {
    const nextQuery = {
      ...clearStudentKnowledgeFocusQuery(rawQuery),
      subjectCode: normalizedSubjectCode,
      subjectId: normalizedSubjectId,
    }
    return {
      path,
      query: sanitizeRouteQuery(nextQuery),
    }
  }

  if (path === '/student/question-bank/repair') {
    const nextQuery = {
      ...clearStudentKnowledgeFocusQuery(rawQuery),
      subjectCode: normalizedSubjectCode,
    }
    return {
      path,
      query: sanitizeRouteQuery(nextQuery),
    }
  }

  if (path === '/student/question-bank/archive') {
    const nextQuery = {
      ...clearStudentKnowledgeFocusQuery(rawQuery),
      subjectCode: normalizedSubjectCode,
    }
    return {
      path,
      query: sanitizeRouteQuery(nextQuery),
    }
  }

  return {
    path,
    query: sanitizeRouteQuery({
      ...rawQuery,
      subjectCode: normalizedSubjectCode,
    }),
  }
}
