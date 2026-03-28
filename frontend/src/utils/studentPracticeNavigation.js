import { sanitizePracticeQuery } from './practiceScope.js'

function toText(value) {
  return String(value || '').trim()
}

function normalizeQuestionIds(questionIds) {
  const sourceRows = Array.isArray(questionIds)
    ? questionIds
    : String(questionIds || '')
      .split(',')
      .map((item) => item.trim())

  return Array.from(new Set(sourceRows.map((item) => toText(item)).filter(Boolean)))
}

export const STUDENT_PRACTICE_SOURCE = Object.freeze({
  TASK: 'TASK',
  WRONG_BOOK: 'WRONG_BOOK',
  KNOWLEDGE: 'KNOWLEDGE',
  HOME: 'HOME',
  POINTS: 'POINTS',
  LEARNING_METHOD: 'LEARNING_METHOD',
})

export const STUDENT_PRACTICE_MODULE = Object.freeze({
  CHAPTER: 'chapter',
  FREE: 'free',
  MOCK: 'mock',
  TASKS: 'tasks',
})

const PRACTICE_SOURCE_DESCRIPTOR_MAP = {
  [STUDENT_PRACTICE_SOURCE.TASK]: {
    title: '今日任务进入',
    description: '当前练习来自知识诊断今日任务，先把今天该拿的分拿下来，再扩展更多练习。',
  },
  [STUDENT_PRACTICE_SOURCE.WRONG_BOOK]: {
    title: '错题修复进入',
    description: '当前练习来自错题修复，优先把反复丢掉的分追回来，段位分会涨得更稳。',
  },
  [STUDENT_PRACTICE_SOURCE.KNOWLEDGE]: {
    title: '知识点专项进入',
    description: '当前练习来自知识诊断定位，适合围绕一个知识点连续击穿，先把短板补成稳定正确输出。',
  },
  [STUDENT_PRACTICE_SOURCE.HOME]: {
    title: '学习首页进入',
    description: '当前练习来自学习首页主线，适合顺着诊断、任务、刷题的节奏快速进入状态。',
  },
  [STUDENT_PRACTICE_SOURCE.POINTS]: {
    title: '积分页进入',
    description: '当前练习来自刷题段位页，适合一边冲积分，一边把正确输出练成升本时能稳定拿分的状态。',
  },
  [STUDENT_PRACTICE_SOURCE.LEARNING_METHOD]: {
    title: '学习方法推荐进入',
    description: '当前练习来自学习方法推荐题包，建议先完成定向题再回到方法页反馈匹配效果。',
  },
}

export function normalizeStudentPracticeSource(value = '') {
  const normalizedValue = toText(value).toUpperCase()
  if (Object.values(STUDENT_PRACTICE_SOURCE).includes(normalizedValue)) {
    return normalizedValue
  }
  return ''
}

export function resolveStudentPracticeSourceDescriptor(source = '', sourceLabel = '') {
  const normalizedSource = normalizeStudentPracticeSource(source)
  const descriptor = PRACTICE_SOURCE_DESCRIPTOR_MAP[normalizedSource]

  if (!descriptor) {
    return {
      key: '',
      title: toText(sourceLabel) || '刷题入口',
      description: '当前练习已统一落到刷题升本主线，可继续按诊断、任务和段位节奏收束范围。',
    }
  }

  return {
    key: normalizedSource,
    title: toText(sourceLabel) || descriptor.title,
    description: descriptor.description,
  }
}

export function buildStudentPracticeRouteLocation({
  module = '',
  subjectCode = '',
  knowledgePathNodeId = '',
  knowledgeId = '',
  chapterCode = '',
  chapterName = '',
  pointCode = '',
  pointName = '',
  pathLabel = '',
  adaptiveQuestionIds = [],
  adaptiveDimension = '',
  adaptiveMastery = '',
  focusMode = '',
  focusQuestionId = '',
  practiceSource = '',
  practiceSourceLabel = '',
  extraQuery = {},
} = {}) {
  const normalizedQuestionIds = normalizeQuestionIds(adaptiveQuestionIds)
  const normalizedPracticeSource = normalizeStudentPracticeSource(practiceSource)
  const normalizedModule = String(module || extraQuery?.module || '').trim().toLowerCase()
  const routePath = normalizedModule === STUDENT_PRACTICE_MODULE.FREE
    ? '/student/practice/free'
    : normalizedModule === STUDENT_PRACTICE_MODULE.MOCK
      ? '/student/practice/mock'
      : normalizedModule === STUDENT_PRACTICE_MODULE.TASKS
        ? '/student/practice/tasks'
      : '/student/practice/chapter'
  const nextQuery = { ...(extraQuery || {}) }
  delete nextQuery.tab
  nextQuery.module = normalizedModule || STUDENT_PRACTICE_MODULE.CHAPTER

  return {
    path: routePath,
    query: sanitizePracticeQuery({
      ...nextQuery,
      subjectCode: toText(subjectCode),
      knowledgePathNodeId: toText(knowledgePathNodeId),
      knowledgeId: toText(knowledgeId),
      chapterCode: toText(chapterCode),
      chapterName: toText(chapterName),
      pointCode: toText(pointCode),
      pointName: toText(pointName),
      pathLabel: toText(pathLabel),
      adaptiveQuestionIds: normalizedQuestionIds.join(','),
      adaptiveDimension: toText(adaptiveDimension),
      adaptiveMastery: toText(adaptiveMastery),
      focusMode: toText(focusMode),
      focusQuestionId: toText(focusQuestionId),
      practiceSource: normalizedPracticeSource,
      practiceSourceLabel: toText(practiceSourceLabel),
    }),
  }
}

export function buildStudentChapterPracticePathLabel({
  subjectName = '',
  subjectCode = '',
  chapterName = '',
} = {}) {
  return [toText(subjectName) || toText(subjectCode), toText(chapterName)].filter(Boolean).join(' / ')
}
