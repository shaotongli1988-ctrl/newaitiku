import axios from 'axios'
import NProgress from 'nprogress'
import { ElMessage, ElMessageBox, ElNotification } from '@/ui/feedback'
import { resolveDevLoginPresetFromLocation } from '../utils/devLogin'
import {
  clearSyncingState,
  finishGlobalRequest,
  setSyncingState,
  startGlobalRequest,
  triggerValidationHighlight,
} from '../utils/uiFeedbackState'

import 'nprogress/nprogress.css'

export const TOKEN_STORAGE_KEY = 'qbAccessToken'
export const ROLE_STORAGE_KEY = 'qbUserRole'
export const USER_ID_STORAGE_KEY = 'qbUserId'
export const ASSIGNED_JOINT_GROUP_STORAGE_KEY = 'qbAssignedJointGroupCode'
const VALID_ROLE_SET = new Set(['super_admin', 'teacher', 'student'])

function readCookie(name) {
  const prefix = `${String(name || '').trim()}=`
  const rows = String(document.cookie || '').split(';')
  for (const row of rows) {
    const normalizedRow = row.trim()
    if (normalizedRow.startsWith(prefix)) {
      return decodeURIComponent(normalizedRow.slice(prefix.length))
    }
  }
  return ''
}

function clearCookie(name) {
  const normalizedName = String(name || '').trim()
  if (!normalizedName) {
    return
  }
  document.cookie = `${normalizedName}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

function readAssignedJointGroupCode() {
  const globalAssignedJointGroupCode = String(window.__QB_ASSIGNED_JOINT_GROUP__ || '').trim()
  if (globalAssignedJointGroupCode) {
    return globalAssignedJointGroupCode
  }
  return String(localStorage.getItem(ASSIGNED_JOINT_GROUP_STORAGE_KEY) || '').trim()
}

function readStoredRole() {
  const storedRole = String(localStorage.getItem(ROLE_STORAGE_KEY) || '').trim()
  if (VALID_ROLE_SET.has(storedRole)) {
    return storedRole
  }
  if (storedRole) {
    localStorage.removeItem(ROLE_STORAGE_KEY)
  }
  return ''
}

export function sanitizeIdentityClientState() {
  const storedRole = String(localStorage.getItem(ROLE_STORAGE_KEY) || '').trim()
  if (storedRole && !VALID_ROLE_SET.has(storedRole)) {
    localStorage.removeItem(ROLE_STORAGE_KEY)
    localStorage.removeItem(USER_ID_STORAGE_KEY)
  }

  const cookieRole = String(readCookie('qbRole') || '').trim()
  if (cookieRole && !VALID_ROLE_SET.has(cookieRole)) {
    clearCookie('qbRole')
    clearCookie('qbUserId')
  }
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY) || ''
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  }
}

export function clearAccessToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

function resolveDirectErrorMessage(error) {
  return String(error?.response?.data?.message || '').trim()
}

export function resolveBackendErrorCode(error) {
  const candidateCode = String(error?.response?.data?.code || error?.response?.data?.errorCode || '').trim()
  return candidateCode ? candidateCode.toUpperCase() : ''
}

export function hasBackendErrorCode(error, code) {
  return resolveBackendErrorCode(error) === String(code || '').trim().toUpperCase()
}

export const backendErrorCodeMessageMap = {
  'AUTH_UNAUTHORIZED': '登录状态已失效，请重新登录。',
  'QUESTION_NOT_FOUND': '请求的资源不存在或已被删除。',
  'QUESTION_FORBIDDEN': '当前账号无权执行该操作。',
  'QUESTION_VALIDATION_FAILED': '请求参数校验失败，请检查后重试。',
  'QUESTION_INVALID_STATUS': '当前操作与资源状态不匹配，请刷新页面后重试。',
  'QUESTION_DATABASE_ERROR': '数据处理失败，请稍后重试。',
  'QUESTION_DEPENDENCY_FAILED': '依赖资源尚未准备完成，请稍后重试。',
  'TASK_NOT_FOUND': '请求的任务不存在或已失效。',
  'TASK_FORBIDDEN': '当前账号无权访问该任务。',
  'TASK_VALIDATION_FAILED': '任务请求参数校验失败，请检查后重试。',
  'ERROR_PROFILE_INCOMPLETE': '当前账号资料未完善，请先补充必要信息。',
}
export const backendErrorCodeValues = [
  'AUTH_UNAUTHORIZED',
  'QUESTION_NOT_FOUND',
  'QUESTION_FORBIDDEN',
  'QUESTION_VALIDATION_FAILED',
  'QUESTION_INVALID_STATUS',
  'QUESTION_DATABASE_ERROR',
  'QUESTION_DEPENDENCY_FAILED',
  'TASK_NOT_FOUND',
  'TASK_FORBIDDEN',
  'TASK_VALIDATION_FAILED',
  'ERROR_PROFILE_INCOMPLETE',
]

export function resolveApiErrorMessage(error, fallback = '请求失败，请稍后重试。') {
  const directMessage = resolveDirectErrorMessage(error)
  if (directMessage) {
    return directMessage
  }
  const backendErrorCode = resolveBackendErrorCode(error)
  if (backendErrorCode && backendErrorCodeMessageMap[backendErrorCode]) {
    return backendErrorCodeMessageMap[backendErrorCode]
  }
  const fallbackMessage = String(error?.message || '').trim()
  if (fallbackMessage) {
    return fallbackMessage
  }
  return String(fallback || '').trim() || '请求失败，请稍后重试。'
}

function resolveErrorMessage(error) {
  return resolveApiErrorMessage(error, '请求失败，请稍后重试。')
}

function normalizeSyncingCode(value) {
  return String(value ?? '')
    .trim()
    .replace(/[\s-]+/g, '_')
    .toUpperCase()
}

export function isExplicitSyncingResponse(error) {
  const statusCode = Number(error?.response?.status || 0)
  if (statusCode === 503) {
    return true
  }
  const responseData = error?.response?.data
  const candidateCodes = [
    responseData?.code,
    responseData?.status,
    responseData?.errorCode,
    responseData?.syncingCode,
  ]
    .map((item) => normalizeSyncingCode(item))
    .filter(Boolean)

  return candidateCodes.some((candidateCode) =>
    ['503', 'SYNCING', 'IS_SYNCING', 'DATA_SYNCING', 'CONTENT_SYNCING', 'SYSTEM_SYNCING', 'SERVICE_UNAVAILABLE'].includes(
      candidateCode,
    ),
  )
}

export function resolveSyncingMessage(error) {
  if (!isExplicitSyncingResponse(error)) {
    return ''
  }
  const directMessage = resolveDirectErrorMessage(error)
  if (directMessage) {
    return directMessage
  }
  return '数据同步中，请稍后重试。'
}

function formatValidationFieldPath(loc) {
  if (!Array.isArray(loc) || loc.length === 0) {
    return 'unknown'
  }

  const segments = loc
    .filter((item) => item !== undefined && item !== null && String(item).trim() !== '')
    .map((item) => String(item).trim())

  if (segments.length === 0) {
    return 'unknown'
  }

  if (['body', 'query', 'path', 'header'].includes(segments[0])) {
    segments.shift()
  }

  if (segments.length === 0) {
    return 'unknown'
  }

  let fieldPath = ''
  segments.forEach((segment, index) => {
    if (/^\d+$/.test(segment)) {
      fieldPath += `[${segment}]`
      return
    }
    if (index === 0 || fieldPath.endsWith(']')) {
      fieldPath += index === 0 ? segment : `.${segment}`
      return
    }
    fieldPath += `.${segment}`
  })

  return fieldPath || 'unknown'
}

export function formatPydanticValidationErrors(detail) {
  if (!Array.isArray(detail)) {
    return []
  }

  const seen = new Set()
  const messages = []

  detail.forEach((item) => {
    const fieldName = formatValidationFieldPath(item?.loc)
    const reason = String(item?.msg || '').trim() || '值不符合校验规则'
    const message = `字段 [${fieldName}] 校验失败：${reason}`
    if (seen.has(message)) {
      return
    }
    seen.add(message)
    messages.push(message)
  })

  return messages
}

function hasExplicitHeader(headers, keyName) {
  if (!headers) {
    return false
  }
  const targetKey = String(keyName || '').toLowerCase()
  return Object.keys(headers).some((headerKey) => String(headerKey || '').toLowerCase() === targetKey)
}

function normalizeRequestPath(url) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) {
    return ''
  }
  if (normalizedUrl.startsWith('/')) {
    return normalizedUrl.split('?')[0]
  }
  try {
    return new URL(normalizedUrl, 'http://127.0.0.1').pathname
  } catch (error) {
    return normalizedUrl.split('?')[0]
  }
}

export function isStudentQuestionBankRequest(config = {}) {
  const requestPath = normalizeRequestPath(config?.url)
  return requestPath.startsWith('/api/question-bank/student/')
}

export function shouldAttachJointGroupHeader(config = {}, storedRole = '', storedAssignedJointGroupCode = '') {
  if (!String(storedAssignedJointGroupCode || '').trim()) {
    return false
  }
  if (hasExplicitHeader(config?.headers, 'X-Joint-Group')) {
    return false
  }
  return String(storedRole || '').trim() === 'student' || isStudentQuestionBankRequest(config)
}

let permissionAlertOpened = false
let loginRedirectTriggered = false
let serverErrorRedirectTriggered = false

function isDevLoginPreview() {
  return Boolean(import.meta.env.DEV && resolveDevLoginPresetFromLocation(window.location.search))
}

export function shouldTrackGlobalLoading(config = {}) {
  return !Boolean(config?.skipGlobalLoading)
}

export function shouldRedirectOnServerError(config = {}) {
  return !Boolean(config?.skipServerErrorRedirect)
}

NProgress.configure({
  showSpinner: false,
  trickleSpeed: 80,
  minimum: 0.08,
})

const resolvedApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

const request = axios.create({
  baseURL: resolvedApiBaseUrl,
  timeout: 15000,
  withCredentials: true,
})

request.interceptors.request.use(
  (config) => {
    sanitizeIdentityClientState()
    if (shouldTrackGlobalLoading(config)) {
      startGlobalRequest()
    }
    if (shouldTrackGlobalLoading(config) && NProgress.status === null) {
      NProgress.start()
    }

    const token = getAccessToken()
    const storedRole = readStoredRole()
    const storedAssignedJointGroupCode = readAssignedJointGroupCode()

    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }

    config.headers = config.headers || {}
    if (shouldAttachJointGroupHeader(config, storedRole, storedAssignedJointGroupCode)) {
      config.headers['X-Joint-Group'] = storedAssignedJointGroupCode
    }

    return config
  },
  (error) => {
    if (shouldTrackGlobalLoading(error?.config)) {
      finishGlobalRequest()
    }
    if (shouldTrackGlobalLoading(error?.config) && NProgress.status !== null) {
      NProgress.done()
    }
    return Promise.reject(error)
  },
)

request.interceptors.response.use(
  (response) => {
    if (shouldTrackGlobalLoading(response?.config)) {
      finishGlobalRequest()
    }
    if (shouldTrackGlobalLoading(response?.config) && NProgress.status !== null) {
      NProgress.done()
    }
    clearSyncingState()
    return response.data
  },
  (error) => {
    if (shouldTrackGlobalLoading(error?.config)) {
      finishGlobalRequest()
    }
    if (shouldTrackGlobalLoading(error?.config) && NProgress.status !== null) {
      NProgress.done()
    }

    const statusCode = error?.response?.status
    const backendErrorCode = resolveBackendErrorCode(error)
    const errorMessage = resolveErrorMessage(error)
    const syncingMessage = resolveSyncingMessage(error)

    if (syncingMessage) {
      setSyncingState({
        visible: true,
        message: syncingMessage,
        statusCode: Number(statusCode || 503),
      })
    } else {
      clearSyncingState()
    }

    if (statusCode === 401) {
      clearAccessToken()
      localStorage.removeItem(ROLE_STORAGE_KEY)
      localStorage.removeItem(USER_ID_STORAGE_KEY)
      const alreadyOnLoginPage = window.location.pathname.startsWith('/login')
      if (!loginRedirectTriggered && !alreadyOnLoginPage) {
        loginRedirectTriggered = true
        ElMessage.warning('登录状态已失效，正在跳转登录页。')
        window.setTimeout(() => {
          const currentPath = `${window.location.pathname || '/'}${window.location.search || ''}${window.location.hash || ''}`
          const loginPath = `/login?redirect=${encodeURIComponent(currentPath)}`
          window.location.assign(loginPath)
        }, 120)
      }
    }

    if (statusCode === 403 || backendErrorCode.endsWith('_FORBIDDEN')) {
      if (isDevLoginPreview()) {
        ElMessage.warning('开发态权限提示：当前资源返回 403，已跳过阻塞弹窗。')
        return Promise.reject(error)
      }
      if (!permissionAlertOpened) {
        permissionAlertOpened = true
        ElMessageBox.alert('当前账号无权限访问该资源，请联系管理员开通权限。', '权限受限', {
          confirmButtonText: '我知道了',
          type: 'warning',
        }).finally(() => {
          permissionAlertOpened = false
        })
      }
    }

    if (
      statusCode === 422
      || backendErrorCode === 'ERROR_PROFILE_INCOMPLETE'
      || backendErrorCode.endsWith('_VALIDATION_FAILED')
      || backendErrorCode.endsWith('_INVALID_STATUS')
    ) {
      if (errorMessage.includes('角色不合法')) {
        sanitizeIdentityClientState()
      }
      const validationMessages = formatPydanticValidationErrors(error?.response?.data?.detail)
      const hasPreciseValidation = validationMessages.length > 0
      const maxVisibleMessages = 6
      const visibleMessages = validationMessages.slice(0, maxVisibleMessages)
      const hiddenCount = Math.max(validationMessages.length - maxVisibleMessages, 0)
      const notificationMessage = hasPreciseValidation
        ? `${visibleMessages.join('\n')}${hiddenCount > 0 ? `\n... 另有 ${hiddenCount} 条校验错误` : ''}`
        : errorMessage || '表单校验失败，请检查输入项后重试。'

      triggerValidationHighlight(validationMessages[0] || notificationMessage)
      ElNotification({
        title: backendErrorCode.endsWith('_INVALID_STATUS') ? '状态流转失败' : '提交数据校验失败',
        message: notificationMessage,
        type: 'warning',
        duration: 6000,
        showClose: true,
      })
    }

    if (statusCode >= 500 && !syncingMessage && shouldRedirectOnServerError(error?.config)) {
      if (!serverErrorRedirectTriggered && !window.location.pathname.startsWith('/error/500')) {
        serverErrorRedirectTriggered = true
        window.location.assign('/error/500')
      }
    }

    return Promise.reject(error)
  },
)

export default request
