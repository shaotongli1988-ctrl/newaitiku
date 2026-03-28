function toText(value) {
  return String(value || '').trim()
}

function isAdvancedMathAlias(subjectCode = '') {
  const normalizedSubjectCode = toText(subjectCode).toUpperCase()
  return normalizedSubjectCode === 'ADVANCED_MATH' || normalizedSubjectCode === 'MATH'
}

export function normalizePracticeSubjectOptions(payload) {
  const coreSubjects = Array.isArray(payload?.coreSubjects) ? payload.coreSubjects : []
  return coreSubjects
    .map((item) => ({
      subjectCode: toText(item?.subjectCode),
      subjectId: toText(item?.subjectId),
      subjectName: toText(item?.subjectName || item?.subjectCode),
      subjectType: toText(item?.subjectType),
      answered: Number(item?.progress?.answered || 0),
      total: Number(item?.progress?.total || 0),
      accuracy: Number(item?.progress?.accuracy || 0),
    }))
    .filter((item) => Boolean(item.subjectCode))
}

export function normalizePracticePercent(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  if (numericValue <= 1) {
    return Math.round(numericValue * 100)
  }
  return Math.round(numericValue)
}

export function resolvePracticeSubjectCode(subjectCode, subjectOptions = []) {
  const normalizedSubjectCode = toText(subjectCode)
  if (!normalizedSubjectCode) {
    return ''
  }

  const normalizedOptions = Array.isArray(subjectOptions) ? subjectOptions : []
  const exactMatch = normalizedOptions.find((item) => toText(item?.subjectCode) === normalizedSubjectCode)
  if (exactMatch) {
    return normalizedSubjectCode
  }

  if (isAdvancedMathAlias(normalizedSubjectCode)) {
    const advancedMathOption = normalizedOptions.find((item) => /^ADVANCED_MATH_[12]$/i.test(toText(item?.subjectCode)))
    if (advancedMathOption?.subjectCode) {
      return toText(advancedMathOption.subjectCode)
    }
  }

  return normalizedSubjectCode
}

export function sanitizePracticeQuery(query) {
  const nextQuery = { ...(query || {}) }
  Object.keys(nextQuery).forEach((key) => {
    const value = nextQuery[key]
    if (value === undefined || value === null || String(value).trim() === '') {
      delete nextQuery[key]
    }
  })
  return nextQuery
}

export function clearPracticePathQuery(query) {
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

export function clearPracticeTransientFocusQuery(query) {
  const nextQuery = { ...(query || {}) }
  delete nextQuery.adaptiveQuestionIds
  delete nextQuery.adaptiveDimension
  delete nextQuery.adaptiveMastery
  delete nextQuery.learningMethodCode
  delete nextQuery.learningMethodRecommendationId
  delete nextQuery.learningMethodSessionId
  delete nextQuery.focusMode
  delete nextQuery.focusQuestionId
  return nextQuery
}
