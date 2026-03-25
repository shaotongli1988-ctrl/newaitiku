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

function normalizeCompleted(value) {
  if (value === true) {
    return true
  }
  if (value === false) {
    return false
  }
  return null
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

export function resolveStudentOnboardingRedirect({ role = '', path = '', userId = '', completed = null } = {}) {
  const normalizedRole = normalizeRole(role)
  const normalizedPath = normalizePath(path)
  const normalizedCompleted = normalizeCompleted(completed)

  if (normalizedRole !== 'student') {
    return ''
  }
  if (!normalizedPath.startsWith('/student/')) {
    return ''
  }
  if (isStudentOnboardingFlowPath(normalizedPath)) {
    return ''
  }
  if (normalizedCompleted === true) {
    return ''
  }
  if (normalizedCompleted === false) {
    return STUDENT_ONBOARDING_ENTRY_PATH
  }
  if (hasStudentOnboardingCompleted(userId)) {
    return ''
  }
  return STUDENT_ONBOARDING_ENTRY_PATH
}
