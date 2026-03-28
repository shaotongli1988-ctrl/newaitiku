function toText(value) {
  return String(value || '').trim()
}

const LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY = 'student_learning_method_feedback_notice'
const MAX_LEARNING_METHOD_FEEDBACK_NOTICE_COUNT = 20

function safeSessionStorage() {
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return null
  }
  return window.sessionStorage
}

function normalizeNoticePayload(payload = {}) {
  const normalizedStatus = toText(payload?.feedbackStatus).toUpperCase()
  if (!normalizedStatus) {
    return null
  }
  return {
    feedbackStatus: normalizedStatus,
    methodCode: toText(payload?.methodCode),
    recommendationId: toText(payload?.recommendationId),
    updateTime: toText(payload?.updateTime) || new Date().toISOString(),
  }
}

function parseStoredNotices(raw) {
  if (!raw) {
    return []
  }
  let parsed
  try {
    parsed = JSON.parse(raw)
  } catch (error) {
    return []
  }
  const source = Array.isArray(parsed) ? parsed : [parsed]
  return source
    .map((item) => normalizeNoticePayload(item))
    .filter(Boolean)
}

function writeNotices(storage, notices) {
  const safeNotices = Array.isArray(notices) ? notices : []
  if (!safeNotices.length) {
    storage.removeItem(LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY)
    return
  }
  storage.setItem(LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY, JSON.stringify(safeNotices))
}

export function saveLearningMethodFeedbackNotice(payload = {}) {
  const storage = safeSessionStorage()
  if (!storage) {
    return
  }
  const nextNotice = normalizeNoticePayload(payload)
  if (!nextNotice) {
    return
  }

  try {
    const existingNotices = parseStoredNotices(
      storage.getItem(LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY),
    )
    const dedupedNotices = existingNotices.filter((item) => (
      String(item.recommendationId || '').trim() !== nextNotice.recommendationId
      || String(item.methodCode || '').trim() !== nextNotice.methodCode
    ))
    const mergedNotices = [...dedupedNotices, nextNotice].slice(-MAX_LEARNING_METHOD_FEEDBACK_NOTICE_COUNT)
    writeNotices(storage, mergedNotices)
  } catch (error) {
    // Ignore storage failure and keep the learning flow usable.
  }
}

export function consumeAllLearningMethodFeedbackNotices() {
  const storage = safeSessionStorage()
  if (!storage) {
    return []
  }
  try {
    const notices = parseStoredNotices(storage.getItem(LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY))
    storage.removeItem(LEARNING_METHOD_FEEDBACK_NOTICE_STORAGE_KEY)
    return notices
  } catch (error) {
    return []
  }
}

export function consumeLearningMethodFeedbackNotice() {
  const notices = consumeAllLearningMethodFeedbackNotices()
  return notices.length ? notices[0] : null
}
