import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'

function toText(value) {
  return String(value || '').trim()
}

function normalizeQuestionIds(questionIds) {
  if (Array.isArray(questionIds)) {
    return questionIds.map((item) => toText(item)).filter((item) => item)
  }
  return toText(questionIds)
    .split(',')
    .map((item) => toText(item))
    .filter((item) => item)
}

export function buildWrongBookPracticeLocation({
  subjectCode = '',
  knowledgeId = '',
  knowledgePathNodeId = '',
  chapterCode = '',
  chapterName = '',
  pointCode = '',
  pointName = '',
  pathLabel = '',
  questionIds = [],
  row = null,
  focusMode = '',
  focusQuestionId = '',
  adaptiveDimension = '',
  adaptiveMastery = 0,
  practiceSourceLabel = '错题修复进入',
} = {}) {
  const normalizedQuestionIds = normalizeQuestionIds(questionIds)
  const rowMeta = row?._meta || {}

  return buildStudentPracticeRouteLocation({
    subjectCode: toText(subjectCode),
    knowledgePathNodeId: toText(knowledgePathNodeId || rowMeta.knowledgePathNodeId),
    knowledgeId: toText(knowledgeId || rowMeta.knowledgeId || row?.knowledgeId),
    chapterCode: toText(chapterCode || rowMeta.chapterCode),
    chapterName: toText(chapterName || rowMeta.chapterLabel || rowMeta.chapter),
    pointCode: toText(pointCode || rowMeta.pointCode),
    pointName: toText(pointName || rowMeta.pointLabel || rowMeta.pointName),
    pathLabel: toText(pathLabel || rowMeta.semanticPath || rowMeta.chapterPointPath || rowMeta.chapter),
    adaptiveDimension: toText(adaptiveDimension || rowMeta.pointCode || rowMeta.pointName || subjectCode || 'ERROR_BOOK'),
    adaptiveQuestionIds: normalizedQuestionIds.join(','),
    adaptiveMastery: Number(adaptiveMastery || rowMeta.masteryScore || 0),
    focusMode: toText(focusMode),
    focusQuestionId: toText(focusQuestionId),
    practiceSource: STUDENT_PRACTICE_SOURCE.WRONG_BOOK,
    practiceSourceLabel,
  })
}

export function buildKnowledgePracticeLocation({
  subjectCode = '',
  row = null,
  practiceSourceLabel = '知识点专项进入',
} = {}) {
  const rowMeta = row?._meta || {}
  return buildStudentPracticeRouteLocation({
    subjectCode: toText(subjectCode || rowMeta.subjectCode),
    chapterCode: toText(rowMeta.chapterCode),
    chapterName: toText(rowMeta.chapterLabel || rowMeta.chapter),
    pointCode: toText(rowMeta.pointCode),
    pointName: toText(rowMeta.pointLabel),
    knowledgeId: toText(rowMeta.knowledgeId || row?.knowledgeId),
    pathLabel: toText(rowMeta.semanticPath || rowMeta.chapter),
    practiceSource: STUDENT_PRACTICE_SOURCE.KNOWLEDGE,
    practiceSourceLabel,
  })
}

export function useStudentQuestionBankNavigation({
  router,
  effectiveSubjectCode,
  buildAnalysisQuery,
} = {}) {
  async function openKnowledgeDiagnosis(extra = {}) {
    await router.push({
      path: '/student/analysis/overview',
      query: typeof buildAnalysisQuery === 'function' ? buildAnalysisQuery(extra) : { ...(extra || {}) },
    })
  }

  async function jumpToWrongBookPractice(options = {}) {
    await router.push(buildWrongBookPracticeLocation({
      ...options,
      subjectCode: toText(options.subjectCode || effectiveSubjectCode?.value),
    }))
  }

  async function jumpToKnowledgePractice(row, options = {}) {
    await router.push(buildKnowledgePracticeLocation({
      row,
      ...options,
      subjectCode: toText(options.subjectCode || effectiveSubjectCode?.value),
    }))
  }

  return {
    openKnowledgeDiagnosis,
    jumpToWrongBookPractice,
    jumpToKnowledgePractice,
  }
}
