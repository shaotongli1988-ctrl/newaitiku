// Observability note: paper service helpers keep log/trace/metric field names stable for release checks.
import request from '../request'
import { assertRequired as assert_required, encodePath as encode_path } from './_shared'

const QUESTION_TYPES = new Set(['single_choice', 'multiple_choice', 'judge', 'subjective'])
const POLICY_VERSION = 'HB_ZSB_2026'

function assert_plain_object(value, field_name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${field_name} must be an object`)
  }
}

function normalize_non_empty_string(value, field_name, min_length = 1, max_length = 999999) {
  const normalized = String(value || '').trim()
  if (normalized.length < min_length || normalized.length > max_length) {
    throw new Error(`${field_name} length must be ${min_length}-${max_length}`)
  }
  return normalized
}

function normalize_integer(value, field_name, min, max = undefined) {
  const normalized = Number(value)
  if (!Number.isInteger(normalized) || normalized < min) {
    throw new Error(`${field_name} must be an integer >= ${min}`)
  }
  if (max !== undefined && normalized > max) {
    throw new Error(`${field_name} must be an integer <= ${max}`)
  }
  return normalized
}

function normalize_boolean(value, field_name, default_value) {
  if (value === undefined) {
    return default_value
  }
  if (typeof value !== 'boolean') {
    throw new Error(`${field_name} must be a boolean`)
  }
  return value
}

function normalize_optional_string(value, field_name, max_length = 999999) {
  if (value === undefined) {
    return undefined
  }
  const normalized = String(value || '').trim()
  if (normalized.length > max_length) {
    throw new Error(`${field_name} max length is ${max_length}`)
  }
  return normalized
}

function normalize_string_id_list(value, field_name) {
  if (!Array.isArray(value)) {
    throw new Error(`${field_name} must be an array`)
  }
  if (value.length === 0) {
    throw new Error(`${field_name} must contain at least one item`)
  }
  const seen = new Set()
  return value.map((item, index) => {
    const normalized = normalize_non_empty_string(item, `${field_name}[${index}]`, 1, 128)
    if (seen.has(normalized)) {
      return null
    }
    seen.add(normalized)
    return normalized
  }).filter((item) => item !== null)
}

function normalize_optional_string_id_list(value, field_name) {
  if (value === undefined) {
    return undefined
  }
  if (!Array.isArray(value)) {
    throw new Error(`${field_name} must be an array`)
  }
  const seen = new Set()
  return value.map((item, index) => {
    const normalized = normalize_non_empty_string(item, `${field_name}[${index}]`, 1, 128)
    if (seen.has(normalized)) {
      return null
    }
    seen.add(normalized)
    return normalized
  }).filter((item) => item !== null)
}

function normalize_question_scores(value, field_name) {
  if (value === undefined) {
    return undefined
  }
  assert_plain_object(value, field_name)
  const normalized = {}
  Object.keys(value).forEach((question_id) => {
    const normalized_question_id = normalize_non_empty_string(question_id, `${field_name}.${question_id}`)
    const score = normalize_integer(value[question_id], `${field_name}.${question_id}`, 1)
    normalized[normalized_question_id] = score
  })
  return normalized
}

function normalize_paper_type_rules(value) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error('typeRules must contain at least one item')
  }
  return value.map((rule, index) => {
    assert_plain_object(rule, `typeRules[${index}]`)
    const type = normalize_non_empty_string(rule.type, `typeRules[${index}].type`)
    if (!QUESTION_TYPES.has(type)) {
      throw new Error(`typeRules[${index}].type is invalid`)
    }
    return {
      type,
      count: normalize_integer(rule.count, `typeRules[${index}].count`, 1),
      questionScore: normalize_integer(rule.questionScore, `typeRules[${index}].questionScore`, 1),
    }
  })
}

function normalize_manual_paper_payload(data) {
  assert_plain_object(data, 'PaperManualModel')
  const examCategoryCode = data.examCategoryCode
  const jointExamGroupCode = data.jointExamGroupCode
  const subjectCode = data.subjectCode
  const policyVersion = data.policyVersion
  const subjectId = normalize_optional_string(data.subjectId, 'subjectId', 128) ?? ''
  const normalized = {
    paperName: normalize_non_empty_string(data.paperName, 'paperName'),
    policyVersion: normalize_non_empty_string(policyVersion ?? 'HB_ZSB_2026', 'policyVersion', 1, 64),
    subjectId,
    examCategoryCode: normalize_non_empty_string(examCategoryCode, 'examCategoryCode', 1, 64),
    jointExamGroupCode: normalize_non_empty_string(jointExamGroupCode, 'jointExamGroupCode', 1, 64),
    subjectCode: normalize_optional_string(subjectCode, 'subjectCode', 64) ?? '',
    paperType: normalize_non_empty_string(data.paperType, 'paperType'),
    paperStatus: normalize_non_empty_string(data.paperStatus, 'paperStatus'),
    durationMinutes: normalize_integer(data.durationMinutes, 'durationMinutes', 1, 240),
    totalScore: normalize_integer(data.totalScore, 'totalScore', 1),
    visibleToStudents: normalize_boolean(data.visibleToStudents, 'visibleToStudents', true),
    questionIds: normalize_string_id_list(data.questionIds, 'questionIds'),
  }
  const rawPublishClassIds = data.publishClassIds ?? data.targetClassIds
  const normalizedPublishClassIds = normalize_optional_string_id_list(rawPublishClassIds, 'publishClassIds')
  if (normalizedPublishClassIds !== undefined) {
    normalized.publishClassIds = normalizedPublishClassIds
  }
  const normalizedQuestionScores = normalize_question_scores(data.questionScores, 'questionScores')
  if (normalizedQuestionScores !== undefined) {
    normalized.questionScores = normalizedQuestionScores
  }
  if (data.paperId !== undefined) {
    normalized.paperId = normalize_optional_string(data.paperId, 'paperId', 128)
  }
  return normalized
}

function normalize_auto_paper_payload(data) {
  assert_plain_object(data, 'PaperAutoModel')
  const manual_form = data.manualForm && typeof data.manualForm === 'object' ? data.manualForm : {}
  const examCategoryCode = data.examCategoryCode ?? manual_form.examCategoryCode
  const jointExamGroupCode = data.jointExamGroupCode ?? manual_form.jointExamGroupCode
  const subjectCode = data.subjectCode ?? manual_form.subjectCode
  const policyVersion = data.policyVersion
  const subjectId = normalize_optional_string(data.subjectId, 'subjectId', 128) ?? ''
  const normalized = {
    paperName: normalize_non_empty_string(data.paperName, 'paperName'),
    policyVersion: normalize_non_empty_string(policyVersion ?? POLICY_VERSION, 'policyVersion', 1, 64),
    paperType: normalize_non_empty_string(data.paperType, 'paperType'),
    paperStatus: normalize_non_empty_string(data.paperStatus, 'paperStatus'),
    durationMinutes: normalize_integer(data.durationMinutes, 'durationMinutes', 1, 240),
    totalScore: normalize_integer(data.totalScore, 'totalScore', 1),
    visibleToStudents: normalize_boolean(data.visibleToStudents, 'visibleToStudents', true),
    subjectId,
    examCategoryCode: normalize_optional_string(examCategoryCode, 'examCategoryCode', 64) ?? '',
    jointExamGroupCode: normalize_optional_string(jointExamGroupCode, 'jointExamGroupCode', 64) ?? '',
    subjectCode: normalize_optional_string(subjectCode, 'subjectCode', 64) ?? '',
    chapter: data.chapter === undefined ? '' : String(data.chapter),
    difficulty: data.difficulty === undefined ? '' : String(data.difficulty),
    typeRules: normalize_paper_type_rules(data.typeRules),
  }
  if (data.paperId !== undefined) {
    normalized.paperId = normalize_optional_string(data.paperId, 'paperId', 128)
  }
  return normalized
}

function normalize_ai_generate_payload(data) {
  assert_plain_object(data, 'PaperAiGenerateModel')
  const subjectId = data.subjectId ?? data.subject_id
  const examCategoryCode = data.examCategoryCode ?? data.exam_category_code
  const jointExamGroupCode = data.jointExamGroupCode ?? data.joint_exam_group_code
  const subjectCode = data.subjectCode ?? data.subject_code
  const policyVersion = data.policyVersion ?? data.policy_version
  const rawClassIds = data.classIds ?? data.class_ids
  const rawKnowledgeScope = data.knowledgeScope ?? data.knowledge_scope
  const rawTotalCount = data.totalCount ?? data.total_count
  const rawDifficulty = data.difficulty ?? data.difficulty_level
  const normalizedClassIds = normalize_optional_string_id_list(rawClassIds, 'classIds')
  const normalizedKnowledgeScope = normalize_optional_string_id_list(rawKnowledgeScope, 'knowledgeScope')
  return {
    policyVersion: normalize_non_empty_string(policyVersion ?? POLICY_VERSION, 'policyVersion', 1, 64),
    subjectId: normalize_optional_string(subjectId, 'subjectId', 128) ?? '',
    examCategoryCode: normalize_optional_string(examCategoryCode, 'examCategoryCode', 64) ?? '',
    jointExamGroupCode: normalize_optional_string(jointExamGroupCode, 'jointExamGroupCode', 64) ?? '',
    subjectCode: normalize_optional_string(subjectCode, 'subjectCode', 64) ?? '',
    classIds: normalizedClassIds === undefined ? [] : normalizedClassIds,
    totalCount: normalize_integer(rawTotalCount, 'totalCount', 10, 50),
    difficulty: normalize_integer(rawDifficulty, 'difficulty', 1, 5),
    knowledgeScope: normalizedKnowledgeScope === undefined ? [] : normalizedKnowledgeScope,
  }
}

export function listPaperQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/papers/questions',
    params,
  })
}

export function saveManualPaper(data) {
  const normalized_data = normalize_manual_paper_payload(data)
  return request({
    method: 'post',
    url: '/api/question-bank/papers/manual',
    data: normalized_data,
  })
}

export function fetchMyClasses() {
  return request({
    method: 'get',
    url: '/api/user/my-classes',
  })
}

export function listTeacherPaperClasses() {
  return request({
    method: 'get',
    url: '/api/question-bank/papers/teacher-classes',
  })
}

export function saveAutoPaper(data) {
  const normalized_data = normalize_auto_paper_payload(data)
  return request({
    method: 'post',
    url: '/api/question-bank/papers/auto',
    data: normalized_data,
  })
}

export function aiGeneratePaper(data) {
  const normalized_data = normalize_ai_generate_payload(data)
  return request({
    method: 'post',
    url: '/api/question-bank/papers/ai-generate',
    data: normalized_data,
  })
}

export function updatePaperStatus(paperId, paperStatus) {
  assert_required(paperId, 'paperId')
  assert_required(paperStatus, 'paperStatus')
  return request({
    method: 'post',
    url: `/api/question-bank/papers/${encode_path(paperId)}/status/${encode_path(paperStatus)}`,
  })
}

export function deletePaper(paperId) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'delete',
    url: `/api/question-bank/papers/${encode_path(paperId)}`,
  })
}

export function restoreDeletedPaper(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: `/api/question-bank/papers/deleted/${encode_path(snapshotId)}/restore`,
  })
}

export function exportPaper(paperId, params = {}) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'get',
    url: `/api/question-bank/papers/${encode_path(paperId)}/export`,
    params,
  })
}

export function paperOverview() {
  return request({
    method: 'get',
    url: '/api/question-bank/papers/overview',
  })
}

export function paperTargetWeights(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/papers/target-weights',
    params,
  })
}

export function paperTemplates() {
  return request({
    method: 'get',
    url: '/api/question-bank/papers/templates',
  })
}

export function savePaperTemplate(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/papers/templates',
    data,
  })
}

export function deletePaperTemplate(templateId) {
  assert_required(templateId, 'templateId')
  return request({
    method: 'delete',
    url: `/api/question-bank/papers/templates/${encode_path(templateId)}`,
  })
}

export function restoreDeletedPaperTemplate(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: `/api/question-bank/papers/templates/deleted/${encode_path(snapshotId)}/restore`,
  })
}
