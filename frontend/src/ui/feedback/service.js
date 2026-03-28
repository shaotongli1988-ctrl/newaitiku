import { reactive } from 'vue'

const DEFAULT_TOAST_DURATION = 2400
let toastSeed = 0
let activeDialogToken = 0

export const feedbackState = reactive({
  toasts: [],
  dialog: {
    visible: false,
    mode: 'alert',
    title: '',
    message: '',
    type: 'info',
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: '',
    inputPlaceholder: '',
    inputError: '',
    inputValidator: null,
    resolver: null,
    rejecter: null,
    closeOnClickModal: true,
    closeOnPressEscape: true,
  },
})

function normalizeText(value) {
  return String(value || '').trim()
}

function normalizeToastPayload(input, fallbackType = 'info') {
  if (typeof input === 'string') {
    return {
      message: input,
      type: fallbackType,
    }
  }
  return {
    message: normalizeText(input?.message),
    type: normalizeText(input?.type) || fallbackType,
    duration: Number(input?.duration),
    showClose: Boolean(input?.showClose),
  }
}

function pushToast(input, fallbackType = 'info') {
  const payload = normalizeToastPayload(input, fallbackType)
  if (!payload.message) {
    return null
  }

  const toastId = `toast-${Date.now()}-${toastSeed += 1}`
  const duration = Number.isFinite(payload.duration) && payload.duration >= 0
    ? payload.duration
    : DEFAULT_TOAST_DURATION

  const toast = {
    id: toastId,
    message: payload.message,
    type: payload.type,
    showClose: payload.showClose,
  }

  feedbackState.toasts.push(toast)

  if (duration > 0 && typeof window !== 'undefined') {
    window.setTimeout(() => {
      closeToast(toastId)
    }, duration)
  }

  return toast
}

export function closeToast(toastId) {
  const targetId = normalizeText(toastId)
  if (!targetId) {
    return
  }
  const nextToasts = feedbackState.toasts.filter((toast) => toast.id !== targetId)
  feedbackState.toasts.splice(0, feedbackState.toasts.length, ...nextToasts)
}

function resetDialog() {
  feedbackState.dialog.visible = false
  feedbackState.dialog.mode = 'alert'
  feedbackState.dialog.title = ''
  feedbackState.dialog.message = ''
  feedbackState.dialog.type = 'info'
  feedbackState.dialog.confirmButtonText = '确定'
  feedbackState.dialog.cancelButtonText = '取消'
  feedbackState.dialog.inputValue = ''
  feedbackState.dialog.inputPlaceholder = ''
  feedbackState.dialog.inputError = ''
  feedbackState.dialog.inputValidator = null
  feedbackState.dialog.resolver = null
  feedbackState.dialog.rejecter = null
  feedbackState.dialog.closeOnClickModal = true
  feedbackState.dialog.closeOnPressEscape = true
}

function openDialog(mode, message, title = '', options = {}) {
  const dialogMessage = normalizeText(message)
  const dialogTitle = normalizeText(title) || '提示'
  const dialogType = normalizeText(options?.type) || 'info'
  const dialogToken = ++activeDialogToken

  if (feedbackState.dialog.visible && typeof feedbackState.dialog.rejecter === 'function') {
    feedbackState.dialog.rejecter('close')
  }

  feedbackState.dialog.visible = true
  feedbackState.dialog.mode = mode
  feedbackState.dialog.title = dialogTitle
  feedbackState.dialog.message = dialogMessage
  feedbackState.dialog.type = dialogType
  feedbackState.dialog.confirmButtonText = normalizeText(options?.confirmButtonText) || '确定'
  feedbackState.dialog.cancelButtonText = normalizeText(options?.cancelButtonText) || '取消'
  feedbackState.dialog.inputValue = normalizeText(options?.inputValue)
  feedbackState.dialog.inputPlaceholder = normalizeText(options?.inputPlaceholder)
  feedbackState.dialog.inputError = ''
  feedbackState.dialog.inputValidator = options?.inputValidator ?? null
  feedbackState.dialog.closeOnClickModal = options?.closeOnClickModal !== false
  feedbackState.dialog.closeOnPressEscape = options?.closeOnPressEscape !== false

  return new Promise((resolve, reject) => {
    feedbackState.dialog.resolver = (payload) => {
      if (dialogToken !== activeDialogToken) {
        return
      }
      resetDialog()
      resolve(payload)
    }
    feedbackState.dialog.rejecter = (reason) => {
      if (dialogToken !== activeDialogToken) {
        return
      }
      resetDialog()
      reject(reason)
    }
  })
}

export function resolveDialog() {
  if (typeof feedbackState.dialog.resolver === 'function') {
    if (feedbackState.dialog.mode === 'prompt') {
      feedbackState.dialog.resolver({
        value: feedbackState.dialog.inputValue,
        action: 'confirm',
      })
      return
    }
    feedbackState.dialog.resolver('confirm')
  }
}

export function rejectDialog(reason = 'cancel') {
  if (typeof feedbackState.dialog.rejecter === 'function') {
    feedbackState.dialog.rejecter(reason)
  }
}

export function validatePromptBeforeResolve() {
  const validator = feedbackState.dialog.inputValidator
  if (typeof validator !== 'function') {
    feedbackState.dialog.inputError = ''
    resolveDialog()
    return
  }

  const validationResult = validator(feedbackState.dialog.inputValue)
  if (validationResult === true || validationResult === undefined) {
    feedbackState.dialog.inputError = ''
    resolveDialog()
    return
  }

  feedbackState.dialog.inputError = normalizeText(validationResult) || '输入内容不符合要求'
}

export const ElMessage = Object.assign(
  (options) => pushToast(options, normalizeText(options?.type) || 'info'),
  {
    success(message) {
      return pushToast(message, 'success')
    },
    warning(message) {
      return pushToast(message, 'warning')
    },
    error(message) {
      return pushToast(message, 'error')
    },
    info(message) {
      return pushToast(message, 'info')
    },
    closeAll() {
      feedbackState.toasts.splice(0, feedbackState.toasts.length)
    },
  },
)

export const ElNotification = Object.assign(
  (options = {}) => pushToast(options, normalizeText(options?.type) || 'info'),
  {
    success(options) {
      return pushToast(options, 'success')
    },
    warning(options) {
      return pushToast(options, 'warning')
    },
    error(options) {
      return pushToast(options, 'error')
    },
    info(options) {
      return pushToast(options, 'info')
    },
  },
)

export const ElMessageBox = {
  alert(message, title = '', options = {}) {
    return openDialog('alert', message, title, options)
  },
  confirm(message, title = '', options = {}) {
    return openDialog('confirm', message, title, options)
  },
  prompt(message, title = '', options = {}) {
    return openDialog('prompt', message, title, options)
  },
}

export function syncDialogInput(value) {
  feedbackState.dialog.inputValue = String(value || '')
  if (feedbackState.dialog.inputError) {
    feedbackState.dialog.inputError = ''
  }
}
