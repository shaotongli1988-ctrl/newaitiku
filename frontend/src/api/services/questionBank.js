import request from '../request'
import {
  assertRequired as assert_required,
  encodePath as encode_path,
  normalizeString as normalize_string,
  unwrapData as unwrap_data,
  unwrapPageData as unwrap_page_data,
} from './_shared'

// questionBank fixed response envelope: { "code": "OK", "message": "success", "data": {} }
const POLICY_VERSION = 'HB_ZSB_2026'

function build_form_data(data = {}, required_fields = []) {
  const form_data = new FormData()
  required_fields.forEach((field_name) => {
    assert_required(data[field_name], field_name)
  })
  Object.entries(data).forEach(([field_name, field_value]) => {
    if (field_value === undefined || field_value === null) {
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
const QUESTION_SNAKE_ALIAS_MAP = Object.fromEntries([
  ['user_id', 'userId'],
  ['knowledge_points', 'knowledgePoints'],
  ['knowledgePointIds', 'knowledgePoints'],
  ['create_time', 'createTime'],
  ['update_time', 'updateTime'],
  ['ext_json', 'extJson'],
  ['exam_category_code', 'examCategoryCode'],
  ['subject_code', 'subjectCode'],
  ['subject_type', 'subjectType'],
  ['joint_exam_group_code', 'jointExamGroupCode'],
  ['module_code', 'moduleCode'],
  ['source_type', 'sourceType'],
  ['policy_version', 'policyVersion'],
  ['policyVersionCode', 'policyVersion'],
  ['stem', 'content'],
  ['optionsJson', 'options'],
])

function assert_plain_object(value, field_name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${field_name} must be an object`)
  }
}

function assert_no_snake_alias_fields(data, model_name) {
  Object.keys(data).forEach((field_name) => {
    if (QUESTION_SNAKE_ALIAS_MAP[field_name]) {
      throw new Error(`${model_name}.${field_name} is not allowed, use ${QUESTION_SNAKE_ALIAS_MAP[field_name]}`)
    }
  })
}

function assert_no_unknown_fields(data, allowed_fields, model_name) {
  Object.keys(data).forEach((field_name) => {
    if (!allowed_fields.has(field_name)) {
      throw new Error(`${model_name}.${field_name} is not defined in app/contracts.py`)
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

  const normalized = {
    title: normalize_non_empty_string(data.title, 'title', 2, 200),
    content: normalize_non_empty_string(data.content, 'content', 1, 5000),
    type: normalize_non_empty_string(data.type, 'type', 1, 64),
    examCategoryCode: normalize_non_empty_string(data.examCategoryCode, 'examCategoryCode', 1, 64),
    jointExamGroupCode: normalize_non_empty_string(data.jointExamGroupCode, 'jointExamGroupCode', 1, 64),
    subjectCode: normalize_non_empty_string(data.subjectCode, 'subjectCode', 1, 64),
    knowledgePoints: normalize_knowledge_points(data.knowledgePoints, { required: true }),
    options: normalize_question_options(data.options || [], 'options'),
    answer: normalize_non_empty_string(data.answer, 'answer', 1, 2000),
    analysis: normalize_optional_string(data.analysis, 'analysis', 0, 5000) ?? '',
    score: data.score === undefined ? 5 : normalize_integer_in_range(data.score, 'score', 1, 100),
    subjectType: normalize_optional_string(data.subjectType, 'subjectType', 0, 64) ?? '',
    moduleCode: normalize_optional_string(data.moduleCode, 'moduleCode', 0, 64) ?? '',
    sourceType: normalize_optional_string(data.sourceType, 'sourceType', 0, 32) ?? 'manual',
    difficulty: normalize_optional_string(data.difficulty, 'difficulty', 1, 32) ?? 'medium',
    status: normalize_optional_string(data.status, 'status', 1, 32) ?? 'DRAFT',
  }
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
  if (data.type !== undefined) normalized.type = normalize_optional_string(data.type, 'type', 1, 64)
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
  if (data.difficulty !== undefined) normalized.difficulty = normalize_optional_string(data.difficulty, 'difficulty', 1, 32)
  if (data.status !== undefined) normalized.status = normalize_optional_string(data.status, 'status', 1, 32)
  if (data.extJson !== undefined) {
    assert_plain_object(data.extJson, 'extJson')
    normalized.extJson = data.extJson
  }
  return normalized
}

/**
 * GET /api/question-bank/admin/console
 * 必填字段: 无
 */
export function adminConsole() {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/console',
  })
}

/**
 * GET /api/question-bank/admin/settings
 * 必填字段: 无
 */
export function adminSettings() {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/settings',
  })
}

/**
 * POST /api/question-bank/admin/settings
 * 必填字段: data
 * Body模型: AdminSystemSettingsSaveRequest
 */
export function saveAdminSettings(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/settings',
    data,
  })
}

/**
 * GET /api/question-bank/admin/students/export
 * 必填字段: 无
 */
export function exportStudents(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/students/export',
    params,
  })
}

/**
 * POST /api/question-bank/admin/students/import
 * 必填字段: data
 * Body模型: AdminStudentsImportRequest
 */
export function importStudents(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/students/import',
    data,
  })
}

/**
 * GET /api/question-bank/admin/users
 * 必填字段: 无
 */
export function listManagedUsers(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/users',
    params,
  })
}

/**
 * POST /api/question-bank/admin/users
 * 必填字段: data
 * Body模型: AdminManagedUserSaveRequest
 */
export function saveManagedUser(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/users',
    data,
  })
}

/**
 * GET /api/question-bank/admin/syllabus
 * 必填字段: 无
 */
export function adminSyllabus() {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/syllabus',
  })
}

/**
 * POST /api/question-bank/admin/syllabus/versions
 * 必填字段: data
 */
export function createAdminSyllabusVersion(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/syllabus/versions',
    data,
  })
}

/**
 * POST /api/question-bank/admin/syllabus/{versionId}/weights
 * 必填字段: versionId, data
 */
export function saveAdminSyllabusWeights(versionId, data) {
  assert_required(versionId, 'versionId')
  return request({
    method: 'post',
    url: '/api/question-bank/admin/syllabus/{versionId}/weights'.replace('{versionId}', encode_path(versionId)),
    data,
  })
}

/**
 * POST /api/question-bank/admin/syllabus/{versionId}/ai-parse
 * 必填字段: versionId, file
 */
export function aiParseAdminSyllabus(versionId, file) {
  assert_required(versionId, 'versionId')
  if (!(file instanceof Blob)) {
    throw new Error('file is required')
  }
  const formData = new FormData()
  formData.append('file', file, typeof file?.name === 'string' ? file.name : 'syllabus.pdf')
  return request({
    method: 'post',
    url: '/api/question-bank/admin/syllabus/{versionId}/ai-parse'.replace('{versionId}', encode_path(versionId)),
    data: formData,
  })
}

/**
 * GET /api/question-bank/analytics/export
 * 必填字段: 无
 */
export function analyticsExport(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/analytics/export',
    params,
  })
}

/**
 * GET /api/question-bank/analytics/records
 * 必填字段: 无
 */
export function listAnalyticsRecords(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/analytics/records',
    params,
  })
}

/**
 * GET /api/question-bank/analytics/summary
 * 必填字段: 无
 */
export function analyticsSummary(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/analytics/summary',
    params,
  })
}

/**
 * POST /api/question-bank/auth/login/password
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function loginByPassword(data) {
  return request({
    method: 'post',
    url: `/api/question-bank/auth/login/password`,
    data,
  })
}

/**
 * POST /api/question-bank/auth/login/sms
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function loginBySms(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/login/sms',
    data,
  })
}

/**
 * POST /api/question-bank/auth/logout
 * 必填字段: 无
 */
export function logout() {
  return request({
    method: 'post',
    url: `/api/question-bank/auth/logout`,
  })
}

/**
 * GET /api/question-bank/auth/me
 * 必填字段: 无
 */
export function authMe() {
  return request({
    method: 'get',
    url: '/api/question-bank/auth/me',
  })
}

/**
 * POST /api/question-bank/auth/password/reset
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function resetPassword(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/password/reset',
    data,
  })
}

/**
 * POST /api/question-bank/auth/register
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function registerUser(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/register',
    data,
  })
}

/**
 * POST /api/question-bank/auth/sms-code
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function sendSmsCode(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/sms-code',
    data,
  })
}

/**
 * GET /api/question-bank/content/baseline
 * 必填字段: 无
 */
export function contentBaseline() {
  return request({
    method: 'get',
    url: '/api/question-bank/content/baseline',
    skipGlobalLoading: true,
  })
}

/**
 * GET /api/question-bank/professional-tree
 * 必填字段: 无
 */
export function professionalTree() {
  return request({
    method: 'get',
    url: '/api/question-bank/professional-tree',
    skipGlobalLoading: true,
  })
}

/**
 * GET /api/question-bank/student/syllabus/catalog
 * 必填字段: 无
 */
export function studentSyllabusCatalog() {
  return request({
    method: 'get',
    url: '/api/question-bank/student/syllabus/catalog',
    skipGlobalLoading: true,
  })
}

/**
 * POST /api/question-bank/imports/template
 * 必填字段: knowledgeId、file
 */
export function importTemplate(data = {}) {
  const form_data = build_form_data(data, ['knowledgeId', 'file'])
  return request({
    method: 'post',
    url: `/api/question-bank/imports/template`,
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * GET /api/question-bank/imports/template/example
 * 必填字段: 无
 */
export function templateImportExample() {
  return request({
    method: 'get',
    url: `/api/question-bank/imports/template/example`,
  })
}

/**
 * POST /api/question-bank/imports/template/preview
 * 必填字段: knowledgeId、file
 */
export function previewTemplateImport(data = {}) {
  const form_data = build_form_data(data, ['knowledgeId', 'file'])
  return request({
    method: 'post',
    url: `/api/question-bank/imports/template/preview`,
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * POST /api/question-bank/batch-parse
 * 必填字段: file
 * 可选字段: examCategoryCode、jointExamGroupCode、subjectCode
 */
export function batchParseQuestions(data = {}) {
  const normalized_data = {
    ...data,
    examCategoryCode: data.examCategoryCode ?? data.examCategoryCode ?? '',
    jointExamGroupCode: data.jointExamGroupCode ?? data.jointExamGroupCode ?? '',
    subjectCode: data.subjectCode ?? data.subjectCode ?? '',
    policyVersion: data.policyVersion ?? data.policyVersion ?? 'HB_ZSB_2026',
  }
  const form_data = build_form_data(
    normalized_data,
    ['file', 'examCategoryCode', 'jointExamGroupCode', 'subjectCode'],
  )
  return request({
    method: 'post',
    url: '/api/question-bank/batch-parse',
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * POST /api/knowledge-graph/parse-from-word
 * 必填字段: file、examCategoryCode、jointExamGroupCode、subjectCode
 */
export function parseKnowledgeGraphFromWord(data = {}) {
  const normalized_data = {
    ...data,
    examCategoryCode: data.examCategoryCode ?? data.examCategoryCode ?? '',
    jointExamGroupCode: data.jointExamGroupCode ?? data.jointExamGroupCode ?? '',
    subjectCode: data.subjectCode ?? data.subjectCode ?? '',
    policyVersion: data.policyVersion ?? data.policyVersion ?? 'HB_ZSB_2026',
  }
  const form_data = build_form_data(
    normalized_data,
    ['file', 'examCategoryCode', 'jointExamGroupCode', 'subjectCode'],
  )
  return request({
    method: 'post',
    url: '/api/knowledge-graph/parse-from-word',
    data: form_data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * POST /api/question-bank/knowledge
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function createKnowledge(data) {
  return request({
    method: 'post',
    url: `/api/question-bank/knowledge`,
    data,
  })
}

/**
 * GET /api/question-bank/knowledge/children
 * 必填字段: 无
 */
export function knowledgeChildren(params = {}) {
  return request({
    method: 'get',
    url: `/api/question-bank/knowledge/children`,
    params,
  })
}

/**
 * POST /api/question-bank/knowledge/deleted/{snapshotId}/restore
 * 必填字段: snapshotId
 */
export function restoreDeletedKnowledge(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: '/api/question-bank/knowledge/deleted/{snapshotId}/restore'.replace('{snapshotId}', encode_path(snapshotId)),
  })
}

/**
 * GET /api/question-bank/knowledge/tree
 * 必填字段: 无
 */
export function knowledgeTree(params = {}) {
  return request({
    method: 'get',
    url: `/api/question-bank/knowledge/tree`,
    params,
    skipGlobalLoading: true,
    skipServerErrorRedirect: true,
  })
}

/**
 * GET /api/knowledge-tree
 * 必填字段: 无
 */
export function knowledgeTreeV2(params = {}) {
  return request({
    method: 'get',
    url: '/api/knowledge-tree',
    params,
    skipServerErrorRedirect: true,
  })
}

/**
 * DELETE /api/question-bank/knowledge/{knowledgeId}
 * 必填字段: knowledgeId
 */
export function deleteKnowledge(knowledgeId) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'delete',
    url: '/api/question-bank/knowledge/{knowledgeId}'.replace('{knowledgeId}', encode_path(knowledgeId)),
  })
}

/**
 * GET /api/question-bank/knowledge/{knowledgeId}
 * 必填字段: knowledgeId
 */
export function getKnowledge(knowledgeId) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'get',
    url: '/api/question-bank/knowledge/{knowledgeId}'.replace('{knowledgeId}', encode_path(knowledgeId)),
  })
}

/**
 * PUT /api/question-bank/knowledge/{knowledgeId}
 * 必填字段: knowledgeId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function updateKnowledge(knowledgeId, data) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'put',
    url: '/api/question-bank/knowledge/{knowledgeId}'.replace('{knowledgeId}', encode_path(knowledgeId)),
    data,
  })
}

/**
 * POST /api/question-bank/knowledge/{knowledgeId}/prerequisites
 * 必填字段: knowledgeId、data.sourceId
 */
export function updateKnowledgePrerequisites(knowledgeId, data) {
  assert_required(knowledgeId, 'knowledgeId')
  return request({
    method: 'post',
    url: '/api/question-bank/knowledge/{knowledgeId}/prerequisites'.replace('{knowledgeId}', encode_path(knowledgeId)),
    data,
  })
}

/**
 * POST /api/question-bank/knowledge/layout
 * 必填字段: data.nodes
 */
export function saveKnowledgeLayout(data) {
  return request({
    method: 'post',
    url: `/api/question-bank/knowledge/layout`,
    data,
  })
}

/**
 * POST /api/question-bank/knowledge/{knowledgeId}/sort/{direction}
 * 必填字段: knowledgeId、direction
 */
export function moveKnowledge(knowledgeId, direction) {
  assert_required(knowledgeId, 'knowledgeId')
  assert_required(direction, 'direction')
  return request({
    method: 'post',
    url: '/api/question-bank/knowledge/{knowledgeId}/sort/{direction}'
      .replace('{knowledgeId}', encode_path(knowledgeId))
      .replace('{direction}', encode_path(direction)),
  })
}

/**
 * GET /api/question-bank/messages
 * 必填字段: 无
 */
export function listMessages(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/messages',
    params,
  })
}

/**
 * POST /api/question-bank/messages/read/batch
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function markMessagesReadBatch(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/messages/read/batch',
    data,
  })
}

/**
 * POST /api/question-bank/messages/send
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function sendMessages(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/messages/send',
    data,
  })
}

/**
 * GET /api/question-bank/messages/send-history
 * 必填字段: 无
 */
export function listMessageSendHistory(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/messages/send-history',
    params,
  })
}

/**
 * POST /api/question-bank/messages/send-history/{traceId}/recall
 * 必填字段: traceId
 */
export function recallMessageSend(traceId) {
  assert_required(traceId, 'traceId')
  return request({
    method: 'post',
    url: '/api/question-bank/messages/send-history/{traceId}/recall'.replace('{traceId}', encode_path(traceId)),
  })
}

/**
 * GET /api/question-bank/messages/settings
 * 必填字段: 无
 */
export function getMessageSettings() {
  return request({
    method: 'get',
    url: '/api/question-bank/messages/settings',
  })
}

/**
 * POST /api/question-bank/messages/settings
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function saveMessageSettings(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/messages/settings',
    data,
  })
}

/**
 * GET /api/question-bank/messages/unread-count
 * 必填字段: 无
 */
export function getMessageUnreadCount() {
  return request({
    method: 'get',
    url: '/api/question-bank/messages/unread-count',
  })
}

/**
 * POST /api/question-bank/messages/{messageId}/read
 * 必填字段: messageId
 */
export function markMessageRead(messageId) {
  assert_required(messageId, 'messageId')
  return request({
    method: 'post',
    url: '/api/question-bank/messages/{messageId}/read'.replace('{messageId}', encode_path(messageId)),
  })
}

/**
 * GET /api/question-bank/messages/teacher-qa/threads
 * 必填字段: 无
 */
export function listTeacherQaThreads(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/messages/teacher-qa/threads',
    params,
  })
}

/**
 * GET /api/question-bank/messages/teacher-qa/threads/{threadId}
 * 必填字段: threadId
 */
export function getTeacherQaThread(threadId) {
  assert_required(threadId, 'threadId')
  return request({
    method: 'get',
    url: '/api/question-bank/messages/teacher-qa/threads/{threadId}'.replace('{threadId}', encode_path(threadId)),
  })
}

/**
 * GET /api/question-bank/messages/teacher-qa/attachments/{attachmentId}
 * 必填字段: attachmentId
 */
export function downloadTeacherQaAttachment(attachmentId) {
  assert_required(attachmentId, 'attachmentId')
  return request({
    method: 'get',
    url: '/api/question-bank/messages/teacher-qa/attachments/{attachmentId}'.replace('{attachmentId}', encode_path(attachmentId)),
    responseType: 'blob',
  })
}

/**
 * POST /api/question-bank/messages/teacher-qa/threads
 * 必填字段: data.subjectCode、data.title
 */
export function createTeacherQaThread(data = {}) {
  const form_data = build_form_data(data, ['subjectCode', 'title'])
  return request({
    method: 'post',
    url: '/api/question-bank/messages/teacher-qa/threads',
    data: form_data,
  })
}

/**
 * POST /api/question-bank/messages/teacher-qa/threads/{threadId}/reply
 * 必填字段: threadId
 */
export function replyTeacherQaThread(threadId, data = {}) {
  assert_required(threadId, 'threadId')
  const form_data = build_form_data(data)
  return request({
    method: 'post',
    url: '/api/question-bank/messages/teacher-qa/threads/{threadId}/reply'.replace('{threadId}', encode_path(threadId)),
    data: form_data,
  })
}

/**
 * POST /api/question-bank/papers/auto
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function saveAutoPaper(data) {
  assert_plain_object(data, 'PaperAutoSaveRequest')
  const manual_form = data.manualForm && typeof data.manualForm === 'object' ? data.manualForm : {}
  const examCategoryCode = (
    data.examCategoryCode
    ?? data.examCategoryCode
    ?? manual_form.examCategoryCode
    ?? manual_form.examCategoryCode
    ?? ''
  )
  const jointExamGroupCode = (
    data.jointExamGroupCode
    ?? data.jointExamGroupCode
    ?? manual_form.jointExamGroupCode
    ?? manual_form.jointExamGroupCode
    ?? ''
  )
  const subjectCode = (
    data.subjectCode
    ?? data.subjectCode
    ?? manual_form.subjectCode
    ?? manual_form.subjectCode
    ?? ''
  )
  const normalized_data = {
    ...data,
    policyVersion: data.policyVersion ?? data.policyVersion ?? data.policyVersionCode ?? POLICY_VERSION,
    examCategoryCode,
    jointExamGroupCode,
    subjectCode,
    examCategoryCode: examCategoryCode,
    jointExamGroupCode: jointExamGroupCode,
    subjectCode: subjectCode,
  }
  return request({
    method: 'post',
    url: `/api/question-bank/papers/auto`,
    data: normalized_data,
  })
}

/**
 * POST /api/question-bank/papers/deleted/{snapshotId}/restore
 * 必填字段: snapshotId
 */
export function restoreDeletedPaper(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: '/api/question-bank/papers/deleted/{snapshotId}/restore'.replace('{snapshotId}', encode_path(snapshotId)),
  })
}

/**
 * POST /api/question-bank/papers/manual
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function saveManualPaper(data) {
  return request({
    method: 'post',
    url: `/api/question-bank/papers/manual`,
    data,
  })
}

/**
 * GET /api/question-bank/papers/overview
 * 必填字段: 无
 */
export function paperOverview() {
  return request({
    method: 'get',
    url: `/api/question-bank/papers/overview`,
  })
}

/**
 * GET /api/question-bank/papers/questions
 * 必填字段: 无
 */
export function listPaperQuestions(params = {}) {
  return request({
    method: 'get',
    url: `/api/question-bank/papers/questions`,
    params,
  })
}

/**
 * GET /api/question-bank/papers/templates
 * 必填字段: 无
 */
export function paperTemplates() {
  return request({
    method: 'get',
    url: `/api/question-bank/papers/templates`,
  })
}

/**
 * POST /api/question-bank/papers/templates
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function savePaperTemplate(data) {
  return request({
    method: 'post',
    url: `/api/question-bank/papers/templates`,
    data,
  })
}

/**
 * POST /api/question-bank/papers/templates/deleted/{snapshotId}/restore
 * 必填字段: snapshotId
 */
export function restoreDeletedPaperTemplate(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: '/api/question-bank/papers/templates/deleted/{snapshotId}/restore'.replace('{snapshotId}', encode_path(snapshotId)),
  })
}

/**
 * DELETE /api/question-bank/papers/templates/{templateId}
 * 必填字段: templateId
 */
export function deletePaperTemplate(templateId) {
  assert_required(templateId, 'templateId')
  return request({
    method: 'delete',
    url: '/api/question-bank/papers/templates/{templateId}'.replace('{templateId}', encode_path(templateId)),
  })
}

/**
 * DELETE /api/question-bank/papers/{paperId}
 * 必填字段: paperId
 */
export function deletePaper(paperId) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'delete',
    url: '/api/question-bank/papers/{paperId}'.replace('{paperId}', encode_path(paperId)),
  })
}

/**
 * GET /api/question-bank/papers/{paperId}/export
 * 必填字段: paperId
 */
export function exportPaper(paperId, params = {}) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'get',
    url: '/api/question-bank/papers/{paperId}/export'.replace('{paperId}', encode_path(paperId)),
    params,
  })
}

/**
 * POST /api/question-bank/papers/{paperId}/status/{paperStatus}
 * 必填字段: paperId、paperStatus
 */
export function updatePaperStatus(paperId, paperStatus) {
  assert_required(paperId, 'paperId')
  assert_required(paperStatus, 'paperStatus')
  return request({
    method: 'post',
    url: '/api/question-bank/papers/{paperId}/status/{paperStatus}'
      .replace('{paperId}', encode_path(paperId))
      .replace('{paperStatus}', encode_path(paperStatus)),
  })
}

/**
 * GET /api/question-bank/questions
 * 必填字段: 无
 */
export function listQuestions(params = {}) {
  return request({
    method: 'get',
    url: `/api/question-bank/questions`,
    params,
  })
}

/**
 * POST /api/question-bank/questions
 * 必填字段: title、content、type、subjectCode、knowledgePoints、answer
 * Body模型: QuestionCreateRequest (snake_case only)
 * 完整 JSON 结构示例:
 * {
 *   "id": "question_001",
 *   "userId": "teacher_001",
 *   "title": "马克思主义认识论单选题",
 *   "content": "马克思主义认识论的核心观点是什么？",
 *   "type": "single_choice",
 *   "subjectCode": "POLITICS",
 *   "knowledgePoints": ["knowledge-point-practice"],
 *   "options": [{"key": "A", "content": "认识来源于权威"}, {"key": "B", "content": "认识源于实践"}],
 *   "answer": "B",
 *   "analysis": "实践是认识的来源。",
  *   "score": 5,
 *   "subjectType": "PUBLIC",
 *   "jointExamGroupCode": "JOINT_EXAM_001",
 *   "moduleCode": "MODULE_001",
 *   "sourceType": "manual",
 *   "difficulty": "medium",
 *   "status": "DRAFT",
 *   "extJson": {"custom_tag": "示例扩展字段"}
 * }
 */
export function createQuestion(data) {
  const normalized_data = normalize_question_create_payload(data)
  return request({
    method: 'post',
    url: `/api/question-bank/questions`,
    data: normalized_data,
  })
}

export function batchCreateQuestions(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/batch-create',
    data,
  })
}

/**
 * POST /api/question-bank/questions/delete/batch
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function deleteQuestionsBatch(data) {
  assert_plain_object(data, 'QuestionDeleteBatchRequest')
  const normalized_data = {
    ...data,
    policyVersion: data.policyVersion ?? data.policyVersion ?? data.policyVersionCode ?? POLICY_VERSION,
  }
  return request({
    method: 'post',
    url: '/api/question-bank/questions/delete/batch',
    data: normalized_data,
  })
}

/**
 * POST /api/question-bank/questions/deleted/batch/{snapshotId}/restore
 * 必填字段: snapshotId
 */
export function restoreDeletedQuestionsBatch(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: '/api/question-bank/questions/deleted/batch/{snapshotId}/restore'.replace('{snapshotId}', encode_path(snapshotId)),
  })
}

/**
 * POST /api/question-bank/questions/deleted/{snapshotId}/restore
 * 必填字段: snapshotId
 */
export function restoreDeletedQuestion(snapshotId) {
  assert_required(snapshotId, 'snapshotId')
  return request({
    method: 'post',
    url: '/api/question-bank/questions/deleted/{snapshotId}/restore'.replace('{snapshotId}', encode_path(snapshotId)),
  })
}

/**
 * POST /api/question-bank/questions/status/batch
 * 必填字段: data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function transitionStatusBatch(data) {
  assert_plain_object(data, 'QuestionStatusBatchTransitionRequest')
  const normalized_data = {
    ...data,
    policyVersion: data.policyVersion ?? data.policyVersion ?? data.policyVersionCode ?? POLICY_VERSION,
  }
  return request({
    method: 'post',
    url: `/api/question-bank/questions/status/batch`,
    data: normalized_data,
  })
}

/**
 * DELETE /api/question-bank/questions/{questionId}
 * 必填字段: questionId
 */
export function deleteQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'delete',
    url: '/api/question-bank/questions/{questionId}'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * GET /api/question-bank/questions/{questionId}
 * 必填字段: questionId
 */
export function getQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: '/api/question-bank/questions/{questionId}'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * PUT /api/question-bank/questions/{questionId}
 * 必填字段: questionId、data
 * Body模型: QuestionUpdateRequest (snake_case only，所有字段可选)
 * 完整 JSON 结构示例:
 * {
 *   "id": "question_001",
 *   "userId": "teacher_001",
 *   "createTime": "2026-03-18T10:00:00+08:00",
 *   "updateTime": "2026-03-18T11:00:00+08:00",
 *   "title": "更新后的题目标题",
 *   "content": "更新后的题干",
 *   "type": "single_choice",
 *   "subjectCode": "POLITICS",
 *   "knowledgePoints": ["knowledge-point-practice"],
 *   "options": [{"key": "A", "content": "选项A"}],
 *   "answer": "A",
 *   "analysis": "更新后的解析",
 *   "score": 10,
 *   "subjectType": "PUBLIC",
 *   "jointExamGroupCode": "JOINT_EXAM_001",
 *   "moduleCode": "MODULE_001",
 *   "sourceType": "manual",
 *   "difficulty": "medium",
 *   "status": "DRAFT",
 *   "extJson": {"custom_tag": "示例扩展字段"}
 * }
 */
export function updateQuestion(questionId, data) {
  assert_required(questionId, 'questionId')
  const normalized_data = normalize_question_update_payload(data)
  return request({
    method: 'put',
    url: '/api/question-bank/questions/{questionId}'.replace('{questionId}', encode_path(questionId)),
    data: normalized_data,
  })
}

/**
 * GET /api/question-bank/questions/{questionId}/reviews
 * 必填字段: questionId
 */
export function listReviews(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: '/api/question-bank/questions/{questionId}/reviews'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * POST /api/question-bank/questions/{questionId}/status/{targetStatus}
 * 必填字段: questionId、targetStatus
 * Body模型: QuestionTransitionRequest (reason)
 */
export function transitionStatus(questionId, targetStatus, data = undefined) {
  assert_required(questionId, 'questionId')
  assert_required(targetStatus, 'targetStatus')
  const normalized_data = data === undefined
    ? { reason: '', policyVersion: POLICY_VERSION }
    : {
      ...data,
      policyVersion: data.policyVersion ?? data.policyVersion ?? data.policyVersionCode ?? POLICY_VERSION,
    }
  return request({
    method: 'post',
    url: '/api/question-bank/questions/{questionId}/status/{targetStatus}'
      .replace('{questionId}', encode_path(questionId))
      .replace('{targetStatus}', encode_path(targetStatus)),
    data: normalized_data,
  })
}

/**
 * POST /api/question-bank/student/check-in
 * 必填字段: 无
 */
export function studentCheckIn() {
  return request({
    method: 'post',
    url: '/api/question-bank/student/check-in',
  })
}

/**
 * GET /api/question-bank/student/dashboard
 * 必填字段: 无
 */
export function studentDashboard() {
  return request({
    method: 'get',
    url: '/api/question-bank/student/dashboard',
  })
}

/**
 * GET /api/question-bank/student/subscription/plans
 * 必填字段: 无
 */
export function listStudentSubscriptionPlans() {
  return request({
    method: 'get',
    url: '/api/question-bank/student/subscription/plans',
  })
}

/**
 * GET /api/question-bank/student/subscription/status
 * 必填字段: 无
 */
export function getStudentSubscriptionStatus() {
  return request({
    method: 'get',
    url: '/api/question-bank/student/subscription/status',
  })
}

/**
 * POST /api/question-bank/student/subscription/redeem
 * 必填字段: code
 */
export function redeemStudentSubscription(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/subscription/redeem',
    data,
  })
}

/**
 * POST /api/question-bank/student/subscription/mock-orders
 * 必填字段: planCode
 */
export function createStudentSubscriptionMockOrder(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/subscription/mock-orders',
    data,
  })
}

/**
 * POST /api/question-bank/student/subscription/mock-orders/{orderId}/confirm
 * 必填字段: orderId、transactionNo
 */
export function confirmStudentSubscriptionMockOrder(orderId, data = {}) {
  assert_required(orderId, 'orderId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/subscription/mock-orders/{orderId}/confirm'.replace('{orderId}', encode_path(orderId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/diagnosis/quick/start
 * 必填字段: 无
 */
export function startStudentQuickDiagnosis(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/diagnosis/quick/start',
    data,
  })
}

/**
 * POST /api/question-bank/student/diagnosis/quick/{sessionId}/submit
 * 必填字段: sessionId、answers
 */
export function submitStudentQuickDiagnosis(sessionId, data = {}) {
  assert_required(sessionId, 'sessionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/diagnosis/quick/{sessionId}/submit'.replace('{sessionId}', encode_path(sessionId)),
    data,
  })
}

/**
 * GET /api/question-bank/student/challenge-points
 * 必填字段: subjectCode
 */
export function studentChallengePoints(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/challenge-points',
    params,
  })
}

/**
 * GET /api/question-bank/student/papers/questions
 * 必填字段: 无
 */
export function listStudentAvailablePaperQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/papers/questions',
    params,
  })
}

/**
 * GET /api/question-bank/student/exam-tasks
 * 必填字段: 无
 */
export function listStudentExamTasks(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/exam-tasks',
    params,
  })
}

/**
 * GET /api/question-bank/student/exam-tasks/{assignmentId}
 * 必填字段: assignmentId
 */
export function getStudentExamTaskDetail(assignmentId) {
  assert_required(assignmentId, 'assignmentId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/exam-tasks/{assignmentId}'.replace('{assignmentId}', encode_path(assignmentId)),
  })
}

/**
 * POST /api/question-bank/student/exam-tasks/{assignmentId}/start
 * 必填字段: assignmentId
 */
export function startStudentExamTask(assignmentId) {
  assert_required(assignmentId, 'assignmentId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/exam-tasks/{assignmentId}/start'.replace('{assignmentId}', encode_path(assignmentId)),
  })
}

/**
 * POST /api/question-bank/student/exam-tasks/{assignmentId}/submit
 * 必填字段: assignmentId、data
 */
export function submitStudentExamTask(assignmentId, data = {}) {
  assert_required(assignmentId, 'assignmentId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/exam-tasks/{assignmentId}/submit'.replace('{assignmentId}', encode_path(assignmentId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/mock-exams/start
 * 必填字段: data
 */
export function startStudentMockExam(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/mock-exams/start',
    data,
  })
}

/**
 * GET /api/question-bank/student/mock-exams/{sessionId}
 * 必填字段: sessionId
 */
export function getStudentMockExamSession(sessionId) {
  assert_required(sessionId, 'sessionId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/mock-exams/{sessionId}'.replace('{sessionId}', encode_path(sessionId)),
  })
}

/**
 * GET /api/question-bank/student/papers/reports
 * 必填字段: 无
 */
export function listStudentPaperReports(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/papers/reports',
    params,
  })
}

/**
 * GET /api/question-bank/student/papers/reports/{reportId}
 * 必填字段: reportId
 */
export function getStudentPaperReportDetail(reportId) {
  assert_required(reportId, 'reportId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/papers/reports/{reportId}'.replace('{reportId}', encode_path(reportId)),
  })
}

/**
 * GET /api/question-bank/student/papers/{paperId}/questions
 * 必填字段: paperId
 */
export function listStudentPaperQuestions(paperId, params = {}) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/papers/{paperId}/questions'.replace('{paperId}', encode_path(paperId)),
    params,
  })
}

/**
 * POST /api/question-bank/student/papers/{paperId}/submit
 * 必填字段: paperId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function submitStudentPaper(paperId, data) {
  assert_required(paperId, 'paperId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/papers/{paperId}/submit'.replace('{paperId}', encode_path(paperId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/papers/{paperId}/questions/{questionId}/check
 * 必填字段: paperId、questionId、data
 */
export function submitStudentPaperQuestion(paperId, questionId, data) {
  assert_required(paperId, 'paperId')
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/papers/{paperId}/questions/{questionId}/check'
      .replace('{paperId}', encode_path(paperId))
      .replace('{questionId}', encode_path(questionId)),
    data,
  })
}

/**
 * GET /api/question-bank/student/personal-bank/export
 * 必填字段: 无
 */
export function studentPersonalBankExport(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/personal-bank/export',
    params,
  })
}

/**
 * GET /api/question-bank/student/personal-bank/questions
 * 必填字段: 无
 */
export function listStudentPersonalBankQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/personal-bank/questions',
    params,
  })
}

/**
 * GET /api/question-bank/student/personal-bank/summary
 * 必填字段: 无
 */
export function studentPersonalBankSummary(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/personal-bank/summary',
    params,
  })
}

/**
 * GET /api/question-bank/student/personal-bank/review-plans
 * 必填字段: 无
 */
export function listStudentPersonalBankReviewPlans(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/personal-bank/review-plans',
    params,
  })
}

/**
 * GET /api/question-bank/student/personal-bank/review-plans/{planId}
 * 必填字段: planId
 */
export function getStudentPersonalBankReviewPlan(planId, params = {}) {
  assert_required(planId, 'planId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/personal-bank/review-plans/{planId}'.replace('{planId}', encode_path(planId)),
    params,
  })
}

/**
 * POST /api/question-bank/student/personal-bank/review-plans/{planId}/start
 * 必填字段: planId
 */
export function startStudentPersonalBankReviewPlan(planId, params = {}) {
  assert_required(planId, 'planId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/personal-bank/review-plans/{planId}/start'.replace('{planId}', encode_path(planId)),
    params,
  })
}

/**
 * POST /api/question-bank/student/personal-bank/review-plans/{planId}/questions/{questionId}/complete
 * 必填字段: planId、questionId
 */
export function completeStudentPersonalBankReviewPlanQuestion(planId, questionId, params = {}) {
  assert_required(planId, 'planId')
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/personal-bank/review-plans/{planId}/questions/{questionId}/complete'
      .replace('{planId}', encode_path(planId))
      .replace('{questionId}', encode_path(questionId)),
    params,
  })
}

/**
 * GET /api/question-bank/student/practice/chapters
 * 必填字段: 无
 */
export function listStudentPracticeChapters(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/practice/chapters',
    params,
  })
}

/**
 * GET /api/question-bank/student/practice/questions
 * 必填字段: 无
 */
export function listStudentPracticeQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/practice/questions',
    params,
  })
}

/**
 * POST /api/question-bank/student/practice/questions/{questionId}/ai-marking
 * 必填字段: questionId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function submitAiMarking(questionId, data) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/practice/questions/{questionId}/ai-marking'.replace('{questionId}', encode_path(questionId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/practice/questions/{questionId}/ai-tutor
 * 必填字段: questionId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function askAiTutor(questionId, data) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/practice/questions/{questionId}/ai-tutor'.replace('{questionId}', encode_path(questionId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/practice/questions/{questionId}/personal-bank
 * 必填字段: questionId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function togglePersonalBankQuestion(questionId, data) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/practice/questions/{questionId}/personal-bank'.replace('{questionId}', encode_path(questionId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/practice/questions/{questionId}/submit
 * 必填字段: questionId、data
 * Body模型: 未在 app/contracts.py 声明 Request 模型
 */
export function submitPracticeAnswer(questionId, data) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/practice/questions/{questionId}/submit'.replace('{questionId}', encode_path(questionId)),
    data,
  })
}

/**
 * POST /api/question-bank/student/practice/questions/{questionId}/wrong-book
 * 必填字段: questionId
 */
export function collectWrongBookQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/practice/questions/{questionId}/wrong-book'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * POST /api/question-bank/student/profile
 * 必填字段: examCategoryCode、jointExamGroupCode
 * Body模型: StudentProfileUpdateRequest (examCategoryCode, jointExamGroupCode)
 */
export function saveStudentProfile(data) {
  assert_plain_object(data, 'StudentProfileUpdateRequest')
  assert_required(data.examCategoryCode, 'examCategoryCode')
  assert_required(data.jointExamGroupCode, 'jointExamGroupCode')
  return request({
    method: 'post',
    url: '/api/question-bank/student/profile',
    data,
  })
}

/**
 * POST /api/question-bank/student/submit
 * 必填字段: answeredCount、elapsedSec
 * Body模型: StudentSessionSubmitRequest (answeredCount, elapsedSec)
 */
export function submitStudentSession(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/submit',
    data,
  })
}

/**
 * POST /api/question-bank/student/wrong-book/papers
 * 必填字段: 无
 */
export function generatePersonalizedWrongBookPaper(params = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/papers',
    params,
  })
}

/**
 * POST /api/question-bank/student/wrong-book/papers/reasoned
 * 必填字段: 无
 */
export function generateReasonedWrongBookPaper(params = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/papers/reasoned',
    params,
  })
}

/**
 * GET /api/question-bank/student/wrong-book/questions
 * 必填字段: 无
 */
export function listWrongBookQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/wrong-book/questions',
    params,
  })
}

/**
 * GET /api/question-bank/student/wrong-book/summary
 * 必填字段: 无
 */
export function getStudentErrorBookSummary(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/student/wrong-book/summary',
    params,
  })
}

/**
 * GET /api/question-bank/teacher/error-book/students
 * 必填字段: 无
 */
export function listTeacherErrorBookStudents() {
  return request({
    method: 'get',
    url: '/api/question-bank/teacher/error-book/students',
  })
}

/**
 * GET /api/question-bank/user/my-classes
 * 必填字段: 无
 */
export function listMyClasses() {
  return request({
    method: 'get',
    url: '/api/question-bank/user/my-classes',
  })
}

/**
 * GET /api/question-bank/teacher/error-book/class-overview
 * 必填字段: 无
 */
export function getTeacherErrorBookClassOverview(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/teacher/error-book/class-overview',
    params,
  })
}

/**
 * POST /api/question-bank/teacher/error-book/class-exports/report
 * 必填字段: 无
 */
export function exportTeacherErrorBookClassReport(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/teacher/error-book/class-exports/report',
    data,
  })
}

/**
 * POST /api/question-bank/teacher/error-book/class-exports/package
 * 必填字段: 无
 */
export function exportTeacherErrorBookClassPackage(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/teacher/error-book/class-exports/package',
    data,
  })
}

/**
 * GET /api/question-bank/teacher/error-book/summary
 * 必填字段: 无
 */
export function getTeacherErrorBookSummary(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/teacher/error-book/summary',
    params,
  })
}

/**
 * GET /api/question-bank/teacher/error-book/questions
 * 必填字段: 无
 */
export function listTeacherErrorBookQuestions(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/teacher/error-book/questions',
    params,
  })
}

/**
 * GET /api/question-bank/teacher/error-book/questions/{questionId}/similar
 * 必填字段: questionId
 */
export function listTeacherSimilarWrongBookQuestions(questionId, params = {}) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: '/api/question-bank/teacher/error-book/questions/{questionId}/similar'.replace('{questionId}', encode_path(questionId)),
    params,
  })
}

/**
 * POST /api/question-bank/teacher/error-book/exports/word
 * 必填字段: 无
 */
export function exportTeacherErrorBookWord(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/teacher/error-book/exports/word',
    data,
  })
}

/**
 * GET /api/question-bank/student/wrong-book/questions/{questionId}/similar
 * 必填字段: questionId
 */
export function listSimilarWrongBookQuestions(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'get',
    url: '/api/question-bank/student/wrong-book/questions/{questionId}/similar'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * POST /api/question-bank/student/wrong-book/exports/word
 * 必填字段: 无
 */
export function exportWrongBookWord(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/exports/word',
    data,
  })
}

/**
 * POST /api/question-bank/student/wrong-book/questions/{questionId}/review
 * 必填字段: questionId
 */
export function reviewWrongBookQuestion(questionId) {
  assert_required(questionId, 'questionId')
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/questions/{questionId}/review'.replace('{questionId}', encode_path(questionId)),
  })
}

/**
 * POST /api/question-bank/student/wrong-book/archive-harvested
 * 必填字段: 无
 */
export function archiveHarvestedWrongBook(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/archive-harvested',
    data,
  })
}

/**
 * POST /api/question-bank/student/wrong-book/restore-archived
 * 必填字段: 无
 */
export function restoreArchivedWrongBook(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/student/wrong-book/restore-archived',
    data,
  })
}

/**
 * GET /api/question-bank/subjects
 * 必填字段: 无
 */
export function listSubjects() {
  return request({
    method: 'get',
    url: '/api/question-bank/subjects',
  })
}

/**
 * GET /api/question-bank/tasks
 * 必填字段: 无
 */
export function listTasks(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/tasks',
    params,
  })
}

/**
 * GET /api/question-bank/exam-tasks
 * 必填字段: 无
 */
export function listExamTasks(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/exam-tasks',
    params,
  })
}

/**
 * POST /api/question-bank/exam-tasks
 * 必填字段: data
 */
export function createExamTask(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/exam-tasks',
    data,
  })
}

/**
 * GET /api/question-bank/exam-tasks/{taskId}
 * 必填字段: taskId
 */
export function getExamTaskDetail(taskId) {
  assert_required(taskId, 'taskId')
  return request({
    method: 'get',
    url: '/api/question-bank/exam-tasks/{taskId}'.replace('{taskId}', encode_path(taskId)),
  })
}

/**
 * GET /api/question-bank/tasks/{taskId}
 * 必填字段: taskId
 */
export function getTask(taskId) {
  assert_required(taskId, 'taskId')
  return request({
    method: 'get',
    url: '/api/question-bank/tasks/{taskId}'.replace('{taskId}', encode_path(taskId)),
  })
}

/**
 * POST /api/question-bank/tasks/{taskId}/cancel
 * 必填字段: taskId
 */
export function cancelTask(taskId) {
  assert_required(taskId, 'taskId')
  return request({
    method: 'post',
    url: '/api/question-bank/tasks/{taskId}/cancel'.replace('{taskId}', encode_path(taskId)),
  })
}

/**
 * POST /api/adaptive-practice/generate
 * 必填字段: 无
 */
export function generateAdaptivePractice(data = {}) {
  return request({
    method: 'post',
    url: '/api/adaptive-practice/generate',
    data,
  })
}

/**
 * GET /api/question-bank/learning-methods
 * 必填字段: 无
 */
export function listLearningMethods(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/learning-methods',
    params,
  })
}

/**
 * GET /api/question-bank/learning-methods/{methodCode}
 * 必填字段: methodCode
 */
export function getLearningMethodDetail(methodCode) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'get',
    url: '/api/question-bank/learning-methods/{methodCode}'.replace('{methodCode}', encode_path(methodCode)),
  })
}

/**
 * POST /api/question-bank/learning-methods/{methodCode}/start
 * 必填字段: methodCode
 */
export function startLearningMethodPractice(methodCode, data = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'post',
    url: '/api/question-bank/learning-methods/{methodCode}/start'.replace('{methodCode}', encode_path(methodCode)),
    data,
  })
}

/**
 * POST /api/question-bank/learning-methods/{methodCode}/complete
 * 必填字段: methodCode
 */
export function completeLearningMethodPractice(methodCode, data = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'post',
    url: '/api/question-bank/learning-methods/{methodCode}/complete'.replace('{methodCode}', encode_path(methodCode)),
    data,
  })
}


/**
 * POST /api/question-bank/admin/learning-methods/{methodCode}/profile/auto-generate
 * 必填字段: methodCode
 */
export function autoGenerateLearningMethodProfile(methodCode, data = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'post',
    url: '/api/question-bank/admin/learning-methods/{methodCode}/profile/auto-generate'.replace('{methodCode}', encode_path(methodCode)),
    data,
  })
}

/**
 * POST /api/question-bank/admin/questions/match-features/auto-batch
 * 必填字段: 无
 */
export function autoBatchQuestionMatchFeatures(data = {}) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/questions/match-features/auto-batch',
    data,
  })
}

/**
 * POST /api/question-bank/learning-methods/{methodCode}/question-pack/recommend
 * 必填字段: methodCode
 */
export function recommendLearningMethodQuestionPack(methodCode, data = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'post',
    url: '/api/question-bank/learning-methods/{methodCode}/question-pack/recommend'.replace('{methodCode}', encode_path(methodCode)),
    data,
  })
}

/**
 * POST /api/question-bank/learning-methods/{methodCode}/question-pack/feedback
 * 必填字段: methodCode
 */
export function feedbackLearningMethodQuestionPack(methodCode, data = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'post',
    url: '/api/question-bank/learning-methods/{methodCode}/question-pack/feedback'.replace('{methodCode}', encode_path(methodCode)),
    data,
  })
}

/**
 * GET /api/question-bank/learning-methods/{methodCode}/question-pack/recommendations
 * 必填字段: methodCode
 */
export function listLearningMethodQuestionPackRecommendations(methodCode, params = {}) {
  assert_required(methodCode, 'methodCode')
  return request({
    method: 'get',
    url: '/api/question-bank/learning-methods/{methodCode}/question-pack/recommendations'.replace('{methodCode}', encode_path(methodCode)),
    params,
  })
}
const KNOWLEDGE_SCOPE_POLICY_VERSION = 'HB_ZSB_2026'

function normalize_knowledge_scope_payload(scope = {}, fallback_scope = {}) {
  const scope_payload = scope && typeof scope === 'object' ? scope : {}
  const fallback_payload = fallback_scope && typeof fallback_scope === 'object' ? fallback_scope : {}

  const examCategoryCode = normalize_string(
    scope_payload.examCategoryCode
    || scope_payload.examCategoryCode
    || fallback_payload.examCategoryCode
    || fallback_payload.examCategoryCode,
  )
  const jointExamGroupCode = normalize_string(
    scope_payload.jointExamGroupCode
    || scope_payload.jointExamGroupCode
    || fallback_payload.jointExamGroupCode
    || fallback_payload.jointExamGroupCode,
  )
  const subjectCode = normalize_string(
    scope_payload.subjectCode
    || scope_payload.subjectCode
    || fallback_payload.subjectCode
    || fallback_payload.subjectCode,
  )
  const policyVersion = normalize_string(
    scope_payload.policyVersion
    || scope_payload.policyVersion
    || fallback_payload.policyVersion
    || fallback_payload.policyVersion
    || KNOWLEDGE_SCOPE_POLICY_VERSION,
  ) || KNOWLEDGE_SCOPE_POLICY_VERSION
  const scope_path = examCategoryCode && jointExamGroupCode && subjectCode
    ? [examCategoryCode, jointExamGroupCode, subjectCode]
    : []

  return {
    examCategoryCode,
    jointExamGroupCode,
    subjectCode,
    policyVersion,
    examCategoryCode: examCategoryCode,
    jointExamGroupCode: jointExamGroupCode,
    subjectCode: subjectCode,
    policyVersion: policyVersion,
    scope_path,
  }
}

function normalize_scope_params(params = {}) {
  return {
    ...params,
    examCategoryCode: normalize_string(params.examCategoryCode),
    jointExamGroupCode: normalize_string(params.jointExamGroupCode),
    subjectCode: normalize_string(params.subjectCode),
  }
}

function normalize_question_list_params(params = {}) {
  const normalized_params = {
    ...params,
    knowledgeId: normalize_string(params.knowledgeId ?? params.knowledge_id),
    questionIds: normalize_string(params.questionIds ?? params.question_ids),
    userId: normalize_string(params.userId ?? params.user_id),
    keyword: normalize_string(params.keyword),
    type: normalize_string(params.type),
    status: normalize_string(params.status),
    chapterCode: normalize_string(params.chapterCode ?? params.chapter_code),
    pointCode: normalize_string(params.pointCode ?? params.point_code),
    examCategoryCode: normalize_string(params.examCategoryCode ?? params.exam_category_code),
    jointExamGroupCode: normalize_string(params.jointExamGroupCode ?? params.joint_exam_group_code),
    subjectCode: normalize_string(params.subjectCode ?? params.subject_code),
    policyVersion: normalize_string(params.policyVersion ?? params.policy_version ?? POLICY_VERSION),
  }

  delete normalized_params.knowledge_id
  delete normalized_params.question_ids
  delete normalized_params.user_id
  delete normalized_params.chapter_code
  delete normalized_params.point_code
  delete normalized_params.exam_category_code
  delete normalized_params.joint_exam_group_code
  delete normalized_params.subject_code
  delete normalized_params.policy_version
  delete normalized_params.policyVersionCode

  return normalized_params
}

function normalize_login_password_payload(payload = {}) {
  return {
    phone: normalize_string(payload.phone),
    password: normalize_string(payload.password),
  }
}

function normalize_message_unread_summary(payload) {
  const data = payload && typeof payload === 'object' ? payload : {}
  return {
    totalUnread: Number(data.totalUnread || data.unreadCount || 0),
  }
}

function normalize_message_list_params(params = {}) {
  return {
    page: Number(params.page || 1),
    size: Number(params.size || 10),
    category: normalize_string(params.category),
    readStatus: normalize_string(params.readStatus),
  }
}

function normalize_message_ids(message_ids = []) {
  if (!Array.isArray(message_ids)) {
    throw new Error('messageIds must be an array')
  }

  const normalized_ids = []
  const seen = new Set()
  message_ids.forEach((item) => {
    const normalized_id = normalize_string(item)
    if (!normalized_id || seen.has(normalized_id)) {
      return
    }
    seen.add(normalized_id)
    normalized_ids.push(normalized_id)
  })
  return normalized_ids
}

function normalize_message_send_at(send_at) {
  const normalized_send_at = normalize_string(send_at)
  if (!normalized_send_at) {
    return ''
  }

  const parsed = new Date(normalized_send_at)
  if (Number.isNaN(parsed.getTime())) {
    return normalized_send_at
  }
  return parsed.toISOString()
}

function normalize_message_send_payload(payload = {}) {
  const normalized_target_mode = normalize_string(payload.targetMode || 'userIds') || 'userIds'
  return {
    targetMode: normalized_target_mode,
    userIds: normalize_message_ids(payload.userIds || []),
    examCategoryCode: normalize_string(payload.examCategoryCode),
    jointExamGroupCode: normalize_string(payload.jointExamGroupCode),
    subjectCode: normalize_string(payload.subjectCode),
    sendAt: normalize_message_send_at(payload.sendAt),
    category: normalize_string(payload.category),
    title: normalize_string(payload.title),
    content: normalize_string(payload.content),
  }
}

const CONTENT_BASELINE_CACHE_KEY = 'qbContentBaselineCacheV1'
const CONTENT_BASELINE_CACHE_TTL_MS = 1000 * 60 * 60 * 12

let content_baseline_memory_cache = null
let content_baseline_inflight_promise = null

function is_object(value) {
  return value !== null && typeof value === 'object'
}

function is_content_baseline_payload_valid(payload) {
  return is_object(payload) && Array.isArray(payload.examCategories)
}

function read_content_baseline_cache_from_storage() {
  if (typeof localStorage === 'undefined') {
    return null
  }

  try {
    const raw_cache = localStorage.getItem(CONTENT_BASELINE_CACHE_KEY)
    if (!raw_cache) {
      return null
    }
    const parsed_cache = JSON.parse(raw_cache)
    const expires_at = Number(parsed_cache?.expiresAt || 0)
    const data = parsed_cache?.data

    if (!Number.isFinite(expires_at) || !is_content_baseline_payload_valid(data)) {
      return null
    }

    return {
      expiresAt: expires_at,
      data,
    }
  } catch (error) {
    return null
  }
}

function write_content_baseline_cache(expires_at, data) {
  if (typeof localStorage === 'undefined') {
    return
  }

  try {
    localStorage.setItem(
      CONTENT_BASELINE_CACHE_KEY,
      JSON.stringify({
        expiresAt: Number(expires_at || 0),
        data,
      }),
    )
  } catch (error) {
    // Ignore storage write errors and keep using in-memory data.
  }
}

function remember_content_baseline(data) {
  const expires_at = Date.now() + CONTENT_BASELINE_CACHE_TTL_MS
  content_baseline_memory_cache = {
    expiresAt: expires_at,
    data,
  }
  write_content_baseline_cache(expires_at, data)
}

function read_valid_content_baseline_cache() {
  const now = Date.now()

  if (
    content_baseline_memory_cache &&
    Number(content_baseline_memory_cache.expiresAt || 0) > now &&
    is_content_baseline_payload_valid(content_baseline_memory_cache.data)
  ) {
    return content_baseline_memory_cache.data
  }

  const persisted_cache = read_content_baseline_cache_from_storage()
  if (persisted_cache && persisted_cache.expiresAt > now) {
    content_baseline_memory_cache = persisted_cache
    return persisted_cache.data
  }

  return null
}

/**
 * Frontend-facing helper exports.
 */
export function fetchStudentDashboard() {
  return studentDashboard().then(unwrap_data)
}

export async function loginWithPassword(payload = {}) {
  const normalized_payload = normalize_login_password_payload(payload)
  assert_required(normalized_payload.phone, 'phone')
  assert_required(normalized_payload.password, 'password')
  const response = await loginByPassword(normalized_payload)
  return unwrap_data(response) || {}
}

export async function fetchContentBaseline(options = {}) {
  const force_refresh = Boolean(options?.forceRefresh)

  if (!force_refresh) {
    const cached_data = read_valid_content_baseline_cache()
    if (cached_data) {
      return cached_data
    }
  }

  if (content_baseline_inflight_promise) {
    return content_baseline_inflight_promise
  }

  const stale_cache = read_content_baseline_cache_from_storage()

  content_baseline_inflight_promise = contentBaseline()
    .then(unwrap_data)
    .then((payload) => {
      if (is_content_baseline_payload_valid(payload)) {
        remember_content_baseline(payload)
      }
      return payload
    })
    .catch((error) => {
      if (!force_refresh && stale_cache && is_content_baseline_payload_valid(stale_cache.data)) {
        return stale_cache.data
      }
      throw error
    })
    .finally(() => {
      content_baseline_inflight_promise = null
    })

  return content_baseline_inflight_promise
}

export async function fetchQuestionList(params) {
  const response = await listQuestions(normalize_question_list_params(params || {}))
  return unwrap_page_data(response)
}

export async function fetchQuestionDetail(questionId) {
  assert_required(questionId, 'questionId')
  const response = await getQuestion(questionId)
  return unwrap_data(response) || {}
}

export async function updateQuestionData(questionId, payload) {
  assert_required(questionId, 'questionId')
  const response = await updateQuestion(questionId, payload)
  return unwrap_data(response) || {}
}

export async function fetchStudentPracticeQuestionList(params) {
  const response = await listStudentPracticeQuestions(normalize_scope_params(params || {}))
  return unwrap_page_data(response)
}

export async function fetchMessageUnreadSummary() {
  const response = await getMessageUnreadCount()
  return normalize_message_unread_summary(unwrap_data(response) || {})
}

export async function fetchMessageListPage(params = {}) {
  const response = await listMessages(normalize_message_list_params(params || {}))
  return unwrap_page_data(response)
}

export async function markMessageAsRead(messageId) {
  assert_required(messageId, 'messageId')
  const response = await markMessageRead(messageId)
  return unwrap_data(response) || {}
}

export async function markMessagesAsReadBatch(messageIds = []) {
  const normalized_ids = normalize_message_ids(messageIds)
  assert_required(normalized_ids[0], 'messageIds[0]')
  const response = await markMessagesReadBatch({ messageIds: normalized_ids })
  return unwrap_data(response) || {}
}

export async function fetchMessageSettings() {
  const response = await getMessageSettings()
  return unwrap_data(response) || {}
}

export async function saveMessageSettingsData(payload = {}) {
  const response = await saveMessageSettings(payload || {})
  return unwrap_data(response) || {}
}

export async function sendMessageBatch(payload = {}) {
  const normalized_payload = normalize_message_send_payload(payload)
  if (normalized_payload.targetMode === 'userIds') {
    assert_required(normalized_payload.userIds[0], 'userIds[0]')
  }
  assert_required(normalized_payload.category, 'category')
  assert_required(normalized_payload.title, 'title')
  assert_required(normalized_payload.content, 'content')
  const response = await sendMessages(normalized_payload)
  return unwrap_data(response) || {}
}

export async function fetchMessageSendHistoryPage(params = {}) {
  const response = await listMessageSendHistory({
    page: Number(params.page || 1),
    size: Number(params.size || 10),
  })
  return unwrap_page_data(response)
}

export async function recallMessageSendRecord(traceId) {
  assert_required(traceId, 'traceId')
  const response = await recallMessageSend(traceId)
  return unwrap_data(response) || {}
}

export async function fetchAdminConsoleData() {
  const response = await adminConsole()
  return unwrap_data(response) || {}
}

export async function saveSystemSettings(payload = {}) {
  const response = await saveAdminSettings(payload || {})
  return unwrap_data(response) || {}
}

export async function fetchManagedUsersPage(params = {}) {
  const response = await listManagedUsers(params || {})
  return unwrap_page_data(response)
}

export async function saveManagedUserRecord(payload = {}) {
  const response = await saveManagedUser(payload || {})
  return unwrap_data(response) || {}
}

export async function importManagedStudents(payload = {}) {
  const response = await importStudents(payload || {})
  return unwrap_data(response) || {}
}

export async function exportManagedStudentsDirectory(params = {}) {
  const response = await exportStudents(params || {})
  return unwrap_data(response) || {}
}

export async function fetchAdminSyllabusData() {
  const response = await adminSyllabus()
  return unwrap_data(response) || {}
}

export async function createSyllabusVersion(payload = {}) {
  const response = await createAdminSyllabusVersion(payload || {})
  return unwrap_data(response) || {}
}

export async function saveSyllabusWeights(versionId, knowledgeWeights = []) {
  assert_required(versionId, 'versionId')
  const response = await saveAdminSyllabusWeights(versionId, { knowledgeWeights })
  return unwrap_data(response) || {}
}

export async function parseSyllabusWithAi(versionId, file) {
  assert_required(versionId, 'versionId')
  const response = await aiParseAdminSyllabus(versionId, file)
  return unwrap_data(response) || {}
}

export async function fetchQuestionReviews(questionId) {
  assert_required(questionId, 'questionId')
  const response = await listReviews(questionId)
  const data = unwrap_data(response)
  return Array.isArray(data) ? data : []
}

export async function updateQuestionStatus(questionId, targetStatus, payload = {}) {
  assert_required(questionId, 'questionId')
  assert_required(targetStatus, 'targetStatus')
  const response = await transitionStatus(questionId, targetStatus, payload)
  return unwrap_data(response) || {}
}

export async function fetchKnowledgeTree(params = {}) {
  const normalized_params = typeof params === 'string'
    ? { status: normalize_string(params) }
    : {
      ...params,
      status: normalize_string(params?.status),
      examCategoryCode: normalize_string(params?.examCategoryCode ?? params?.examCategoryCode),
      jointExamGroupCode: normalize_string(params?.jointExamGroupCode ?? params?.jointExamGroupCode),
      subjectCode: normalize_string(params?.subjectCode ?? params?.subjectCode),
      policyVersion: normalize_string(params?.policyVersion ?? params?.policyVersion),
    }
  const response = await knowledgeTree(normalized_params)
  const data = unwrap_data(response)
  if (Array.isArray(data)) {
    return data
  }
  const graph = data && typeof data === 'object' ? data : {}
  const nodes = Array.isArray(graph.nodes) ? graph.nodes : []
  const links = Array.isArray(graph.links) ? graph.links : []
  const node_map = {}
  nodes.forEach((node) => {
    const id = normalize_string(node?.id)
    if (!id) {
      return
    }
    node_map[id] = {
      id,
      name: normalize_string(node?.label || id),
      mastery: Number(node?.mastery || 0),
      size: Number(node?.size || 8),
      children: [],
    }
  })
  const child_ids = new Set()
  links.forEach((link) => {
    if (!link || link.type !== 'parent') {
      return
    }
    const source = normalize_string(link.source)
    const target = normalize_string(link.target)
    if (!source || !target || !node_map[source] || !node_map[target] || source === target) {
      return
    }
    node_map[source].children.push(node_map[target])
    child_ids.add(target)
  })
  return Object.keys(node_map)
    .filter((id) => !child_ids.has(id))
    .map((id) => node_map[id])
}

export async function parseKnowledgeGraphFromWordFile(data = {}) {
  const request_scope = normalize_knowledge_scope_payload({}, data)
  const response = await parseKnowledgeGraphFromWord({
    ...data,
    examCategoryCode: data.examCategoryCode ?? data.examCategoryCode ?? request_scope.examCategoryCode,
    jointExamGroupCode:
      data.jointExamGroupCode ?? data.jointExamGroupCode ?? request_scope.jointExamGroupCode,
    subjectCode: data.subjectCode ?? data.subjectCode ?? request_scope.subjectCode,
    policyVersion: data.policyVersion ?? data.policyVersion ?? KNOWLEDGE_SCOPE_POLICY_VERSION,
  })
  const payload = unwrap_data(response) || {}
  const normalized_scope = normalize_knowledge_scope_payload(payload.scope, request_scope)
  return {
    ...payload,
    scope: normalized_scope,
    scope_path: normalized_scope.scope_path,
    examCategoryCode: normalized_scope.examCategoryCode,
    jointExamGroupCode: normalized_scope.jointExamGroupCode,
    subjectCode: normalized_scope.subjectCode,
    policyVersion: normalized_scope.policyVersion,
    examCategoryCode: normalized_scope.examCategoryCode,
    jointExamGroupCode: normalized_scope.jointExamGroupCode,
    subjectCode: normalized_scope.subjectCode,
    policyVersion: normalized_scope.policyVersion,
    hb_zsb_2026_scope: normalized_scope,
  }
}

export async function parseQuestionBatchFromWordFile(data = {}) {
  const request_scope = normalize_knowledge_scope_payload({}, data)
  const response = await batchParseQuestions({
    ...data,
    examCategoryCode: data.examCategoryCode ?? data.examCategoryCode ?? request_scope.examCategoryCode,
    jointExamGroupCode:
      data.jointExamGroupCode ?? data.jointExamGroupCode ?? request_scope.jointExamGroupCode,
    subjectCode: data.subjectCode ?? data.subjectCode ?? request_scope.subjectCode,
    policyVersion: data.policyVersion ?? data.policyVersion ?? KNOWLEDGE_SCOPE_POLICY_VERSION,
  })
  const payload = unwrap_data(response) || {}
  console.log('=== parseQuestionBatchFromWordFile 调试 ===')
  console.log('unwrap_data 结果:', payload)
  console.log('payload.items:', payload?.items)
  console.log('payload.items长度:', payload?.items?.length)
  console.log('=== 调试结束 ===')
  
  const normalized_scope = normalize_knowledge_scope_payload(payload.scope, request_scope)
  return {
    ...payload,
    scope: normalized_scope,
    scope_path: normalized_scope.scope_path,
    examCategoryCode: normalized_scope.examCategoryCode,
    jointExamGroupCode: normalized_scope.jointExamGroupCode,
    subjectCode: normalized_scope.subjectCode,
    policyVersion: normalized_scope.policyVersion,
    hb_zsb_2026_scope: normalized_scope,
  }
}

export async function moveKnowledgeNode(knowledgeId, direction) {
  assert_required(knowledgeId, 'knowledgeId')
  assert_required(direction, 'direction')
  const response = await moveKnowledge(knowledgeId, direction)
  return unwrap_data(response) || {}
}

export async function fetchTaskList(params) {
  const response = await listTasks(params || {})
  return unwrap_page_data(response)
}

export async function fetchTaskProgress(taskId) {
  assert_required(taskId, 'taskId')
  const response = await getTask(taskId)
  return unwrap_data(response) || {}
}

export async function createStudentSession(payload = {}) {
  const answered_count = Number(payload.answeredCount || 0)
  const elapsed_sec = Number(payload.elapsedSec || 0)
  const response = await submitStudentSession({
    answeredCount: Number.isFinite(answered_count) ? Math.max(0, answered_count) : 0,
    elapsedSec: Number.isFinite(elapsed_sec) ? Math.max(0, elapsed_sec) : 0,
  })
  const data = unwrap_data(response) || {}
  const sessionId = normalize_string(payload.sessionId || `session-${Date.now()}`)
  return {
    sessionId: sessionId,
    answeredCount: Number(data.answeredCount || 0),
    elapsedSec: Number(data.elapsedSec || 0),
    updateTime: normalize_string(data.updateTime),
  }
}

export async function getStudentSession(sessionId) {
  assert_required(sessionId, 'sessionId')
  const response = await studentDashboard()
  const data = unwrap_data(response) || {}
  const session = data.examSession && typeof data.examSession === 'object' ? data.examSession : {}
  return {
    sessionId: normalize_string(sessionId),
    answeredCount: Number(session.answeredCount || 0),
    elapsedSec: Number(session.elapsedSec || 0),
    updateTime: normalize_string(session.updateTime),
  }
}

export async function updateStudentSessionAnswer(sessionId, questionId, payload = {}) {
  assert_required(sessionId, 'sessionId')
  assert_required(questionId, 'questionId')
  const normalized_answer = normalize_string(payload.answer)
  assert_required(normalized_answer, 'answer')
  const elapsed_sec = Number(payload.elapsedSec || 0)
  const answered_count = Number(payload.answeredCount || 0)
  const sourceType = normalize_string(payload.sourceType)
  const attemptId = normalize_string(payload.attemptId || payload.attemptKey || payload.submissionId)

  const answer_response = await submitPracticeAnswer(questionId, {
    answer: normalized_answer,
    elapsedSec: Number.isFinite(elapsed_sec) ? Math.max(0, elapsed_sec) : 0,
    sourceType: sourceType,
    attemptId,
  })

  const session_response = await submitStudentSession({
    answeredCount: Number.isFinite(answered_count) ? Math.max(0, answered_count) : 0,
    elapsedSec: Number.isFinite(elapsed_sec) ? Math.max(0, elapsed_sec) : 0,
  })

  const answer_data = unwrap_data(answer_response) || {}
  const session_data = unwrap_data(session_response) || {}
  return {
    sessionId: normalize_string(sessionId),
    questionId: normalize_string(questionId),
    answer: normalize_string(answer_data.answer || normalized_answer),
    isCorrect: Boolean(answer_data.isCorrect),
    challengePointDelta: Number(answer_data.challengePointDelta || 0),
    challengePointGranted: Boolean(answer_data.challengePointGranted),
    challengePointTotal: Number(answer_data.challengePointTotal || 0),
    subjectRank: Number(answer_data.subjectRank || 0),
    challengePoints: answer_data.challengePoints && typeof answer_data.challengePoints === 'object'
      ? answer_data.challengePoints
      : {},
    challengeAwardGranted: Boolean(answer_data.challengeAwardGranted),
    answeredCount: Number(session_data.answeredCount || 0),
    elapsedSec: Number(session_data.elapsedSec || 0),
    updateTime: normalize_string(session_data.updateTime),
  }
}

export async function submitAiTutorTask(questionId, payload) {
  assert_required(questionId, 'questionId')
  const response = await askAiTutor(questionId, payload)
  return unwrap_data(response) || {}
}

export async function submitAiMarkingTask(questionId, payload) {
  assert_required(questionId, 'questionId')
  const response = await submitAiMarking(questionId, payload)
  return unwrap_data(response) || {}
}

export async function fetchAnalyticsSummary(params) {
  const response = await analyticsSummary(params || {})
  return unwrap_data(response) || {}
}

export async function fetchAnalyticsRecords(params) {
  const response = await listAnalyticsRecords(params || {})
  return unwrap_page_data(response)
}

export async function fetchAnalyticsExport(params) {
  const response = await analyticsExport(params || {})
  return unwrap_data(response) || {}
}

export async function fetchAdaptivePracticeList(payload = {}) {
  const response = await generateAdaptivePractice(payload || {})
  return unwrap_data(response) || {}
}

export async function fetchLearningMethodList(params = {}) {
  const response = await listLearningMethods(params || {})
  const data = unwrap_data(response)
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
    }
  }
  if (data && typeof data === 'object') {
    const items = Array.isArray(data.items) ? data.items : []
    return {
      ...data,
      items,
      total: Number(data.total || items.length || 0),
    }
  }
  return {
    items: [],
    total: 0,
  }
}

export async function fetchLearningMethodDetail(methodCode) {
  assert_required(methodCode, 'methodCode')
  const response = await getLearningMethodDetail(methodCode)
  return unwrap_data(response) || {}
}

export async function startLearningMethodSession(methodCode, payload = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await startLearningMethodPractice(methodCode, payload || {})
  return unwrap_data(response) || {}
}

export async function completeLearningMethodSession(methodCode, payload = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await completeLearningMethodPractice(methodCode, payload || {})
  return unwrap_data(response) || {}
}


export async function runAutoGenerateLearningMethodProfile(methodCode, payload = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await autoGenerateLearningMethodProfile(methodCode, payload || {})
  return unwrap_data(response) || {}
}

export async function runAutoBatchQuestionMatchFeatures(payload = {}) {
  const response = await autoBatchQuestionMatchFeatures(payload || {})
  return unwrap_data(response) || {}
}

export async function fetchLearningMethodQuestionPackRecommendation(methodCode, payload = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await recommendLearningMethodQuestionPack(methodCode, payload || {})
  return unwrap_data(response) || {}
}

export async function submitLearningMethodQuestionPackFeedback(methodCode, payload = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await feedbackLearningMethodQuestionPack(methodCode, payload || {})
  return unwrap_data(response) || {}
}

export async function fetchLearningMethodQuestionPackRecommendationHistory(methodCode, params = {}) {
  assert_required(methodCode, 'methodCode')
  const response = await listLearningMethodQuestionPackRecommendations(methodCode, params || {})
  const data = unwrap_data(response)
  if (Array.isArray(data)) {
    return { items: data, total: data.length }
  }
  if (data && typeof data === 'object') {
    return {
      ...data,
      items: Array.isArray(data.items) ? data.items : [],
      total: Number(data.total || 0),
    }
  }
  return { items: [], total: 0 }
}
export async function persistKnowledgeGraphLayout(nodes = []) {
  const normalized_nodes = Array.isArray(nodes)
    ? nodes
        .map((item) => ({
          id: normalize_string(item?.id),
          x: Number(item?.x),
          y: Number(item?.y),
        }))
        .filter((item) => item.id && Number.isFinite(item.x) && Number.isFinite(item.y))
    : []
  if (!normalized_nodes.length) {
    return { updatedCount: 0, updatedIds: [] }
  }
  const response = await saveKnowledgeLayout({ nodes: normalized_nodes })
  return unwrap_data(response) || {}
}
