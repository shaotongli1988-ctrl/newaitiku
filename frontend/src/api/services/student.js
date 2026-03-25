import {
  analyticsExport,
  analyticsSummary,
  askAiTutor,
  confirmStudentSubscriptionMockOrder,
  createStudentSubscriptionMockOrder,
  getStudentSubscriptionStatus,
  getMessageSettings,
  getMessageUnreadCount,
  getTask,
  listStudentSubscriptionPlans,
  listAnalyticsRecords,
  listMessageSendHistory,
  listMessages,
  listStudentPracticeChapters,
  listStudentPracticeQuestions,
  listTasks,
  markMessageRead,
  markMessagesReadBatch,
  recallMessageSend as recallMessageSendApi,
  redeemStudentSubscription,
  saveMessageSettings as saveMessageSettingsApi,
  sendMessages as sendMessagesApi,
  startStudentQuickDiagnosis,
  studentDashboard,
  submitAiMarking,
  submitStudentQuickDiagnosis,
  cancelTask as cancelTaskApi,
  studentChallengePoints,
} from './questionBank'
import {
  assertRequired as assert_required,
  normalizeString as normalize_string,
  unwrapData as unwrap_data,
  unwrapPageData as unwrap_page_data,
} from './_shared'
import { normalizeAnalyticsSummary } from '../../utils/analyticsSummary'

function normalize_scope_params(params = {}) {
  return {
    ...params,
    examCategoryCode: normalize_string(params.examCategoryCode),
    jointExamGroupCode: normalize_string(params.jointExamGroupCode),
    subjectCode: normalize_string(params.subjectCode),
  }
}

function normalize_task_payload(payload) {
  const normalized = payload && typeof payload === 'object' ? { ...payload } : {}
  const taskId = normalize_string(normalized.taskId || normalized.id)
  if (taskId) {
    normalized.id = taskId
    normalized.taskId = taskId
  }
  if ('progress' in normalized) {
    const progress = Number(normalized.progress)
    normalized.progress = Number.isFinite(progress) ? progress : 0
  }
  return normalized
}

function normalize_ai_quota(quota_payload) {
  const payload = quota_payload && typeof quota_payload === 'object' ? quota_payload : {}
  const daily_limit = Number(payload.dailyLimit || 0)
  const used_count = Number(payload.usedCount || 0)
  return {
    dailyLimit: Number.isFinite(daily_limit) ? daily_limit : 0,
    usedCount: Number.isFinite(used_count) ? used_count : 0,
  }
}

export async function fetchStudentDashboard() {
  const response = await studentDashboard()
  return unwrap_data(response) || {}
}

export async function fetchStudentSubscriptionPlans() {
  const response = await listStudentSubscriptionPlans()
  const data = unwrap_data(response)
  return Array.isArray(data) ? data : []
}

export async function fetchStudentSubscriptionStatus() {
  const response = await getStudentSubscriptionStatus()
  return unwrap_data(response) || {}
}

export async function redeemStudentSubscriptionCode(payload = {}) {
  const response = await redeemStudentSubscription(payload || {})
  return unwrap_data(response) || {}
}

export async function createStudentSubscriptionOrder(payload = {}) {
  const response = await createStudentSubscriptionMockOrder(payload || {})
  return unwrap_data(response) || {}
}

export async function confirmStudentSubscriptionOrder(orderId, payload = {}) {
  assert_required(orderId, 'orderId')
  const response = await confirmStudentSubscriptionMockOrder(orderId, payload || {})
  return unwrap_data(response) || {}
}

export async function startStudentQuickDiagnosisSession(payload = {}) {
  const response = await startStudentQuickDiagnosis(payload || {})
  return unwrap_data(response) || {}
}

export async function submitStudentQuickDiagnosisSession(sessionId, payload = {}) {
  assert_required(sessionId, 'sessionId')
  const response = await submitStudentQuickDiagnosis(sessionId, payload || {})
  return unwrap_data(response) || {}
}

export async function fetchStudentChallengePoints(params = {}) {
  const response = await studentChallengePoints(params || {})
  return unwrap_data(response) || {}
}

export async function fetchStudentPracticeChapterList(params = {}) {
  const response = await listStudentPracticeChapters(params || {})
  const data = unwrap_data(response)
  return Array.isArray(data) ? data : []
}

export async function fetchStudentPracticeQuestionList(params = {}) {
  const response = await listStudentPracticeQuestions(normalize_scope_params(params || {}))
  return unwrap_page_data(response)
}

export async function submitAiMarkingTask(questionId, payload) {
  assert_required(questionId, 'questionId')
  const response = await submitAiMarking(questionId, payload)
  return normalize_task_payload(unwrap_data(response) || {})
}

export async function submitAiTutorTask(questionId, payload) {
  assert_required(questionId, 'questionId')
  const response = await askAiTutor(questionId, payload)
  return normalize_task_payload(unwrap_data(response) || {})
}

export async function fetchTaskList(params = {}) {
  const response = await listTasks(params || {})
  const data = unwrap_data(response) || {}
  const page_data = unwrap_page_data(response)
  return {
    ...page_data,
    items: page_data.items.map((item) => normalize_task_payload(item)),
    aiQuota: normalize_ai_quota(data.aiQuota),
  }
}

export async function fetchTaskDetail(taskId) {
  assert_required(taskId, 'taskId')
  const response = await getTask(taskId)
  return normalize_task_payload(unwrap_data(response) || {})
}

export async function fetchTaskProgress(taskId) {
  return fetchTaskDetail(taskId)
}

export async function cancelTask(taskId) {
  assert_required(taskId, 'taskId')
  const response = await cancelTaskApi(taskId)
  return normalize_task_payload(unwrap_data(response) || {})
}

export async function fetchAnalyticsSummary(params = {}) {
  const response = await analyticsSummary(normalize_scope_params(params || {}))
  return normalizeAnalyticsSummary(unwrap_data(response) || {})
}

export async function fetchAnalyticsRecords(params = {}) {
  const response = await listAnalyticsRecords(normalize_scope_params(params || {}))
  return unwrap_page_data(response)
}

export async function fetchAnalyticsExport(params = {}) {
  const response = await analyticsExport(normalize_scope_params(params || {}))
  return unwrap_data(response) || {}
}

export async function fetchMessageList(params = {}) {
  const response = await listMessages(params || {})
  return unwrap_page_data(response)
}

export async function markMessageAsRead(messageId) {
  assert_required(messageId, 'messageId')
  const response = await markMessageRead(messageId)
  return unwrap_data(response) || {}
}

export async function markMessagesAsReadBatch(payload) {
  const response = await markMessagesReadBatch(payload || {})
  return unwrap_data(response) || {}
}

export async function fetchMessageUnreadCount() {
  const response = await getMessageUnreadCount()
  return unwrap_data(response) || {}
}

export async function fetchMessageSettings() {
  const response = await getMessageSettings()
  return unwrap_data(response) || {}
}

export async function saveMessageSettings(payload) {
  const response = await saveMessageSettingsApi(payload || {})
  return unwrap_data(response) || {}
}

export async function sendMessages(payload) {
  const response = await sendMessagesApi(payload || {})
  return unwrap_data(response) || {}
}

export async function fetchMessageSendHistory(params = {}) {
  const response = await listMessageSendHistory(params || {})
  return unwrap_page_data(response)
}

export async function recallMessageSend(traceId) {
  assert_required(traceId, 'traceId')
  const response = await recallMessageSendApi(traceId)
  return unwrap_data(response) || {}
}
