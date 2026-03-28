// Observability note: question service helpers keep log/trace/metric field names stable for release checks.
import request from '../request'
import { assertRequired as assert_required, encodePath as encode_path } from './_shared'

const QUESTION_TYPES = new Set(['single_choice', 'multiple_choice', 'judge', 'subjective'])
const QUESTION_DIFFICULTIES = new Set(['easy', 'medium', 'hard'])
const QUESTION_STATUSES = new Set(['DRAFT', 'QA_IN_PROGRESS', 'REVIEW_PENDING', 'PUBLISHED', 'REJECTED'])
const QUESTION_OBJECTIVE_TYPES = new Set(['single_choice', 'multiple_choice', 'judge'])
const POLICY_VERSION = 'HB_ZSB_2026'

const QUESTION_CREATE_REQUIRED_FIELDS = [
  'title',
  'content',
  'type',
  'examCategoryCode',
  'jointExamGroupCode',
  'subjectCode',
  'knowledgePoints',
  'answer',
]
const QUESTION_CREATE_ALLOWED_FIELDS = new Set([
  'id',
  'userId',
  'title',
  'content',
  'type',
  'examCategoryCode',
  'subjectCode',
  'knowledgePoints',
  'options',
  'answer',
  'analysis',
  'score',
  'subjectType',
  'jointExamGroupCode',
  'moduleCode',
  'sourceType',
  'difficulty',
  'status',
  'extJson',
])

const QUESTION_UPDATE_ALLOWED_FIELDS = new Set([
  'id',
  'userId',
  'createTime',
  'updateTime',
  'title',
  'content',
  'type',
  'examCategoryCode',
  'subjectCode',
  'knowledgePoints',
  'options',
  'answer',
  'analysis',
  'score',
  'subjectType',
  'jointExamGroupCode',
  'moduleCode',
  'sourceType',
  'difficulty',
  'status',
  'extJson',
])

const QUESTION_SNAKE_ALIAS_MAP = {
  user_id: 'userId',
  knowledge_points: 'knowledgePoints',
  knowledgePointIds: 'knowledgePoints',
  stem: 'content',
  optionsJson: 'options',
  create_time: 'createTime',
  update_time: 'updateTime',
  ext_json: 'extJson',
  exam_category_code: 'examCategoryCode',
  subject_code: 'subjectCode',
  subject_type: 'subjectType',
  joint_exam_group_code: 'jointExamGroupCode',
  module_code: 'moduleCode',
  source_type: 'sourceType',
  policy_version: 'policyVersion',
  policyVersionCode: 'policyVersion',
}

function assert_plain_object(value, field_name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${field_name} must be an object`)
  }
}

function assert_no_unknown_fields(data, allowed_fields, model_name) {
  Object.keys(data).forEach((field_name) => {
    if (!allowed_fields.has(field_name)) {
      throw new Error(`${model_name}.${field_name} is not defined in app/contracts.py`)
    }
  })
}

function assert_no_snake_alias_fields(data, model_name) {
  Object.keys(data).forEach((field_name) => {
    if (QUESTION_SNAKE_ALIAS_MAP[field_name]) {
      throw new Error(`${model_name}.${field_name} is not allowed, use ${QUESTION_SNAKE_ALIAS_MAP[field_name]}`)
    }
  })
}

function normalize_non_empty_string(value, field_name, min_length = 1, max_length = 999999) {
  const normalized = String(value || '').trim()
  if (normalized.length < min_length || normalized.length > max_length) {
    throw new Error(`${field_name} length must be ${min_length}-${max_length}`)
  }
  return normalized
}

function normalize_optional_string(value, field_name, min_length = 0, max_length = 999999) {
  if (value === undefined) {
    return undefined
  }
  const normalized = String(value || '').trim()
  if (normalized.length < min_length || normalized.length > max_length) {
    throw new Error(`${field_name} length must be ${min_length}-${max_length}`)
  }
  return normalized
}

function normalize_integer_in_range(value, field_name, min, max) {
  const normalized = Number(value)
  if (!Number.isInteger(normalized) || normalized < min || normalized > max) {
    throw new Error(`${field_name} must be an integer in ${min}-${max}`)
  }
  return normalized
}

function normalize_question_options(value, field_name = 'options') {
  if (!Array.isArray(value)) {
    throw new Error(`${field_name} must be an array`)
  }
  return value.map((item, index) => {
    assert_plain_object(item, `${field_name}[${index}]`)
    return {
      key: normalize_non_empty_string(item.key, `${field_name}[${index}].key`, 1, 8),
      content: normalize_non_empty_string(item.content, `${field_name}[${index}].content`, 1, 500),
    }
  })
}

function normalize_knowledge_points(value, { required }) {
  if (!Array.isArray(value)) {
    throw new Error('knowledgePoints must be an array')
  }
  const normalized = value.map((item) => String(item || '').trim()).filter((item) => item)
  if (required && normalized.length === 0) {
    throw new Error('knowledgePoints must contain at least one item')
  }
  if (normalized.length > 20) {
    throw new Error('knowledgePoints max length is 20')
  }
  return normalized
}

function assert_question_enum_membership(value, field_name, enum_values) {
  if (!enum_values.has(value)) {
    throw new Error(`${field_name} is invalid`)
  }
}

function normalize_question_create_payload(data) {
  assert_plain_object(data, 'QuestionCreateRequest')
  assert_no_snake_alias_fields(data, 'QuestionCreateRequest')
  assert_no_unknown_fields(data, QUESTION_CREATE_ALLOWED_FIELDS, 'QuestionCreateRequest')

  QUESTION_CREATE_REQUIRED_FIELDS.forEach((field_name) => {
    if (field_name === 'knowledgePoints') {
      if (!Array.isArray(data.knowledgePoints)) {
        throw new Error('knowledgePoints is required')
      }
      return
    }
    assert_required(data[field_name], field_name)
  })

  const type = normalize_non_empty_string(data.type, 'type', 1, 64)
  assert_question_enum_membership(type, 'type', QUESTION_TYPES)
  const options = normalize_question_options(data.options || [], 'options')
  if (QUESTION_OBJECTIVE_TYPES.has(type) && options.length === 0) {
    throw new Error('options must contain at least one item for objective questions')
  }

  const normalized = {
    title: normalize_non_empty_string(data.title, 'title', 2, 200),
    content: normalize_non_empty_string(data.content, 'content', 1, 5000),
    type,
    examCategoryCode: normalize_non_empty_string(data.examCategoryCode, 'examCategoryCode', 1, 64),
    jointExamGroupCode: normalize_non_empty_string(data.jointExamGroupCode, 'jointExamGroupCode', 1, 64),
    subjectCode: normalize_non_empty_string(data.subjectCode, 'subjectCode', 1, 64),
    knowledgePoints: normalize_knowledge_points(data.knowledgePoints, { required: true }),
    options,
    answer: normalize_non_empty_string(data.answer, 'answer', 1, 2000),
    analysis: normalize_optional_string(data.analysis, 'analysis', 0, 5000) ?? '',
    score: data.score === undefined ? 5 : normalize_integer_in_range(data.score, 'score', 1, 100),
    subjectType: normalize_optional_string(data.subjectType, 'subjectType', 0, 64) ?? '',
    moduleCode: normalize_optional_string(data.moduleCode, 'moduleCode', 0, 64) ?? '',
    sourceType: normalize_optional_string(data.sourceType, 'sourceType', 0, 32) ?? 'manual',
    difficulty: normalize_optional_string(data.difficulty, 'difficulty', 1, 32) ?? 'medium',
    status: normalize_optional_string(data.status, 'status', 1, 32) ?? 'DRAFT',
  }

  assert_question_enum_membership(normalized.difficulty, 'difficulty', QUESTION_DIFFICULTIES)
  assert_question_enum_membership(normalized.status, 'status', QUESTION_STATUSES)

  if (data.extJson !== undefined) {
    assert_plain_object(data.extJson, 'extJson')
    normalized.extJson = data.extJson
  } else {
    normalized.extJson = {}
  }
  if (data.id !== undefined) {
    normalized.id = normalize_optional_string(data.id, 'id', 1, 128)
  }
  if (data.userId !== undefined) {
    normalized.userId = normalize_optional_string(data.userId, 'userId', 1, 128)
  }
  return normalized
}

function normalize_question_update_payload(data) {
  assert_plain_object(data, 'QuestionUpdateRequest')
  assert_no_snake_alias_fields(data, 'QuestionUpdateRequest')
  assert_no_unknown_fields(data, QUESTION_UPDATE_ALLOWED_FIELDS, 'QuestionUpdateRequest')

  const normalized = {}
  if (data.id !== undefined) normalized.id = normalize_optional_string(data.id, 'id', 1, 128)
  if (data.userId !== undefined) normalized.userId = normalize_optional_string(data.userId, 'userId', 1, 128)
  if (data.createTime !== undefined) normalized.createTime = normalize_optional_string(data.createTime, 'createTime', 1, 64)
  if (data.updateTime !== undefined) normalized.updateTime = normalize_optional_string(data.updateTime, 'updateTime', 1, 64)
  if (data.title !== undefined) normalized.title = normalize_optional_string(data.title, 'title', 2, 200)
  if (data.content !== undefined) normalized.content = normalize_optional_string(data.content, 'content', 1, 5000)
  if (data.type !== undefined) {
    normalized.type = normalize_optional_string(data.type, 'type', 1, 64)
    assert_question_enum_membership(normalized.type, 'type', QUESTION_TYPES)
  }
  if (data.examCategoryCode !== undefined) {
    normalized.examCategoryCode = normalize_optional_string(data.examCategoryCode, 'examCategoryCode', 1, 64)
  }
  if (data.subjectCode !== undefined) normalized.subjectCode = normalize_optional_string(data.subjectCode, 'subjectCode', 1, 64)
  if (data.knowledgePoints !== undefined) normalized.knowledgePoints = normalize_knowledge_points(data.knowledgePoints, { required: false })
  if (data.options !== undefined) normalized.options = normalize_question_options(data.options, 'options')
  if (data.answer !== undefined) normalized.answer = normalize_optional_string(data.answer, 'answer', 1, 2000)
  if (data.analysis !== undefined) normalized.analysis = normalize_optional_string(data.analysis, 'analysis', 0, 5000)
  if (data.score !== undefined) normalized.score = normalize_integer_in_range(data.score, 'score', 1, 100)
  if (data.subjectType !== undefined) normalized.subjectType = normalize_optional_string(data.subjectType, 'subjectType', 0, 64)
  if (data.jointExamGroupCode !== undefined) {
    normalized.jointExamGroupCode = normalize_optional_string(data.jointExamGroupCode, 'jointExamGroupCode', 0, 64)
  }
  if (data.moduleCode !== undefined) normalized.moduleCode = normalize_optional_string(data.moduleCode, 'moduleCode', 0, 64)
  if (data.sourceType !== undefined) normalized.sourceType = normalize_optional_string(data.sourceType, 'sourceType', 0, 32)
  if (data.difficulty !== undefined) {
    normalized.difficulty = normalize_optional_string(data.difficulty, 'difficulty', 1, 32)
    assert_question_enum_membership(normalized.difficulty, 'difficulty', QUESTION_DIFFICULTIES)
  }
  if (data.status !== undefined) {
    normalized.status = normalize_optional_string(data.status, 'status', 1, 32)
    assert_question_enum_membership(normalized.status, 'status', QUESTION_STATUSES)
  }
  if (data.extJson !== undefined) {
    assert_plain_object(data.extJson, 'extJson')
    normalized.extJson = data.extJson
  }
  return normalized
}

function normalize_question_transition_payload(data = undefined) {
  if (data === undefined) {
    return { reason: '', policyVersion: POLICY_VERSION }
  }
  assert_plain_object(data, 'QuestionTransitionRequest')
  const reason = data.reason === undefined ? '' : String(data.reason)
  const policyVersion = normalize_non_empty_string(
    data.policyVersion ?? POLICY_VERSION,
    'policyVersion',
    1,
    64,
  )
  return { reason, policyVersion }
}

function build_form_data(data = {}, required_fields = []) {
  const form_data = new FormData()
  required_fields.forEach((field_name) => {
    assert_required(data[field_name], field_name)
  })
  Object.entries(data).forEach(([field_name, field_value]) => {
    if (field_value === undefined || field_value === null) {
      return
    }
    if (field_name === 'selectedIndexes') {
      if (!Array.isArray(field_value)) {
        throw new Error('selectedIndexes must be an array')
      }
      field_value.forEach((item, index) => {
        const normalized = Number(item)
        if (!Number.isInteger(normalized) || normalized < 0) {
          throw new Error(`selectedIndexes[${index}] must be a non-negative integer`)
        }
        form_data.append(field_name, String(normalized))
      })
      return
    }
    if (Array.isArray(field_value)) {
      field_value.forEach((item) => {
        form_data.append(field_name, item instanceof Blob ? item : String(item))
      })
      return
    }
    form_data.append(field_name, field_value instanceof Blob ? field_value : String(field_value))
  })
  return form_data
}

export function listQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/questions',
    params,
  })
}

export function getQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: `/api/question-bank/questions/${encode_path(questionId)}`,
  })
}

export function createQuestion(data) {
  const normalized_data = normalize_question_create_payload(data)
  return request({
    method: 'post',
    url: '/api/question-bank/questions',
    data: normalized_data,
  })
}

export function updateQuestion(questionId, data) {
  assert_required(questionId, 'questionId')
  const normalized_data = normalize_question_update_payload(data)
  return request({
    method: 'put',
    url: `/api/question-bank/questions/${encode_path(questionId)}`,
    data: normalized_data,
  })
}

export function deleteQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'delete',
    url: `/api/question-bank/questions/${encode_path(questionId)}`,
  })
}

export function listReviews(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: `/api/question-bank/questions/${encode_path(questionId)}/reviews`,
  })
}

export function transitionStatus(questionId, targetStatus, data = undefined) {
  assert_required(questionId, 'questionId')
  assert_required(targetStatus, 'targetStatus')
  const normalized_data = normalize_question_transition_payload(data)
  return request({
    method: 'post',
    url: `/api/question-bank/questions/${encode_path(questionId)}/status/${encode_path(targetStatus)}`,
    data: normalized_data,
  })
}

export function transitionStatusBatch(data) {
  assert_plain_object(data, 'QuestionStatusBatchTransitionRequest')
  const normalized_data = {
    ...data,
    policyVersion: normalize_non_empty_string(
      data.policyVersion ?? POLICY_VERSION,
      'policyVersion',
      1,
      64,
    ),
  }
  return request({
    method: 'post',
    url: '/api/question-bank/questions/status/batch',
    data: normalized_data,
  })
}

export function createKnowledge(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/knowledge',
    data,
  })
}

export function getKnowledge(knowledgeId) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'get',
    url: `/api/question-bank/knowledge/${encode_path(knowledgeId)}`,
  })
}

export function updateKnowledge(knowledgeId, data) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'put',
    url: `/api/question-bank/knowledge/${encode_path(knowledgeId)}`,
    data,
  })
}

export function updateKnowledgePrerequisites(knowledgeId, data) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'post',
    url: `/api/question-bank/knowledge/${encode_path(knowledgeId)}/prerequisites`,
    data,
  })
}

export function saveKnowledgeLayout(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/knowledge/layout',
    data,
  })
}

export function deleteKnowledge(knowledgeId) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'delete',
    url: `/api/question-bank/knowledge/${encode_path(knowledgeId)}`,
  })
}

export function restoreDeletedKnowledge(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: `/api/question-bank/knowledge/deleted/${encode_path(snapshotId)}/restore`,
  })
}

export function knowledgeTree(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/knowledge/tree',
    params,
    skipGlobalLoading: true,
    skipServerErrorRedirect: true,
  })
}

export function knowledgeChildren(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/knowledge/children',
    params,
  })
}

export function moveKnowledge(knowledgeId, direction) {
  assert_required(knowledgeId, 'knowledgeId')
  assert_required(direction, 'direction')
  return request({
    method: 'post',
    url: `/api/question-bank/knowledge/${encode_path(knowledgeId)}/sort/${encode_path(direction)}`,
  })
}

export function importTemplate(data = {}) {
  const form_data = build_form_data(data, ['knowledgeId', 'file'])
  return request({
    method: 'post',
    url: '/api/question-bank/imports/template',
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function previewTemplateImport(data = {}) {
  const form_data = build_form_data(data, ['knowledgeId', 'file'])
  return request({
    method: 'post',
    url: '/api/question-bank/imports/template/preview',
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function templateImportExample() {
  return request({
    method: 'get',
    url: '/api/question-bank/imports/template/example',
  })
}
