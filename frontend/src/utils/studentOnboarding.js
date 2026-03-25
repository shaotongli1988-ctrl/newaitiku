const STUDENT_ONBOARDING_STORAGE_PREFIX = 'qbStudentOnboardingCompleted'
const STUDENT_ONBOARDING_ENTRY_PATH = '/student/onboarding/diagnosis'

function normalizePath(path = '') {
  return String(path || '').trim()
}

function normalizeRole(role = '') {
  return String(role || '').trim()
}

function normalizeUserId(userId = '') {
  return String(userId || '').trim()
}

function resolveStorageKey(userId = '') {
  const normalizedUserId = normalizeUserId(userId)
  if (!normalizedUserId) {
    return STUDENT_ONBOARDING_STORAGE_PREFIX
  }
  return `${STUDENT_ONBOARDING_STORAGE_PREFIX}:${normalizedUserId}`
}

function canUseStorage() {
  return typeof localStorage !== 'undefined'
}

export function isStudentOnboardingFlowPath(path = '') {
  const normalizedPath = normalizePath(path)
  if (!normalizedPath.startsWith('/student/')) {
    return false
  }
  return normalizedPath.startsWith('/student/onboarding/') || normalizedPath.startsWith('/student/subscription/')
}

export function hasStudentOnboardingCompleted(userId = '') {
  if (!canUseStorage()) {
    return false
  }
  return localStorage.getItem(resolveStorageKey(userId)) === '1'
}

export function markStudentOnboardingCompleted(userId = '') {
  if (!canUseStorage()) {
    return
  }
  localStorage.setItem(resolveStorageKey(userId), '1')
}

export function clearStudentOnboardingCompleted(userId = '') {
  if (!canUseStorage()) {
    return
  }
  localStorage.removeItem(resolveStorageKey(userId))
}

export function resolveStudentOnboardingRedirect({ role = '', path = '', userId = '' } = {}) {
  const normalizedRole = normalizeRole(role)
  const normalizedPath = normalizePath(path)

  if (normalizedRole !== 'student') {
    return ''
  }
  if (!normalizedPath.startsWith('/student/')) {
    return ''
  }
  if (isStudentOnboardingFlowPath(normalizedPath)) {
    return ''
  }
  if (hasStudentOnboardingCompleted(userId)) {
    return ''
  }
  return STUDENT_ONBOARDING_ENTRY_PATH
}
