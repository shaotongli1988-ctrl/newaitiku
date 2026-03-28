export const QUESTION_TYPE_LABEL_MAP = {
  single_choice: '单选题',
  multiple_choice: '多选题',
  judge: '判断题',
  subjective: '主观题',
}

export const QUESTION_DIFFICULTY_LABEL_MAP = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

export const QUESTION_STATUS_META = {
  DRAFT: {
    label: '草稿',
    type: 'info',
    color: '#64748b',
  },
  QA_IN_PROGRESS: {
    label: 'QA 互审中',
    type: 'warning',
    color: '#f59e0b',
  },
  REVIEW_PENDING: {
    label: '待终审',
    type: 'primary',
    color: '#3b82f6',
  },
  PUBLISHED: {
    label: '已发布',
    type: 'success',
    color: '#059669',
  },
  REJECTED: {
    label: '已驳回',
    type: 'danger',
    color: '#ef4444',
  },
}

export const questionStatusValues = ['DRAFT', 'QA_IN_PROGRESS', 'REVIEW_PENDING', 'PUBLISHED', 'REJECTED']

export const questionTransitionEdges = [
  'DRAFT>QA_IN_PROGRESS',
  'DRAFT>REVIEW_PENDING',
  'DRAFT>REJECTED',
  'QA_IN_PROGRESS>REVIEW_PENDING',
  'QA_IN_PROGRESS>REJECTED',
  'REVIEW_PENDING>PUBLISHED',
  'REVIEW_PENDING>REJECTED',
  'REJECTED>DRAFT',
]

export const allowedTransitions = {
  'DRAFT': ['QA_IN_PROGRESS', 'REVIEW_PENDING', 'REJECTED'],
  'QA_IN_PROGRESS': ['REVIEW_PENDING', 'REJECTED'],
  'REVIEW_PENDING': ['PUBLISHED', 'REJECTED'],
  'REJECTED': ['DRAFT'],
  'PUBLISHED': [],
}

export function questionTypeLabel(type) {
  return QUESTION_TYPE_LABEL_MAP[String(type || '').trim()] || String(type || '-')
}

export function questionDifficultyLabel(difficulty) {
  const normalizedDifficulty = String(difficulty || '').trim().toLowerCase()
  return QUESTION_DIFFICULTY_LABEL_MAP[normalizedDifficulty] || String(difficulty || '-')
}

export function questionStatusMeta(status) {
  return QUESTION_STATUS_META[String(status || '').trim()] || QUESTION_STATUS_META.DRAFT
}

export function canTransitionQuestionStatus(currentStatus, targetStatus) {
  const normalizedCurrentStatus = String(currentStatus || '').trim()
  const normalizedTargetStatus = String(targetStatus || '').trim()
  return Array.isArray(allowedTransitions[normalizedCurrentStatus])
    && allowedTransitions[normalizedCurrentStatus].includes(normalizedTargetStatus)
}

export function parseOptionsJson(optionsJson) {
  try {
    const parsed = JSON.parse(String(optionsJson || '[]'))
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    return []
  }
}

export function parseExtJson(extJson) {
  if (extJson && typeof extJson === 'object' && !Array.isArray(extJson)) {
    return extJson
  }
  try {
    const parsed = JSON.parse(String(extJson || '{}'))
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    return {}
  }
}

export function reviewStatusLabel(status) {
  const statusMeta = questionStatusMeta(status)
  return statusMeta?.label || String(status || '-')
}
