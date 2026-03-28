import { reactive } from 'vue'

export const uiFeedbackState = reactive({
  pendingRequestCount: 0,
  validationEpoch: 0,
  lastValidationMessage: '',
  isSyncing: false,
  syncingMessage: '',
  syncingStatusCode: 0,
})

function normalizeCount(value) {
  const parsed = Number(value || 0)
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0
  }
  return Math.floor(parsed)
}

export function startGlobalRequest() {
  uiFeedbackState.pendingRequestCount = normalizeCount(uiFeedbackState.pendingRequestCount) + 1
}

export function finishGlobalRequest() {
  const currentCount = normalizeCount(uiFeedbackState.pendingRequestCount)
  uiFeedbackState.pendingRequestCount = currentCount > 0 ? currentCount - 1 : 0
}

export function setSyncingState({ visible = false, message = '', statusCode = 0 } = {}) {
  uiFeedbackState.isSyncing = Boolean(visible)
  uiFeedbackState.syncingMessage = String(message || '').trim()
  uiFeedbackState.syncingStatusCode = normalizeCount(statusCode)
}

export function clearSyncingState() {
  setSyncingState()
}

export function triggerValidationHighlight(message = '') {
  uiFeedbackState.validationEpoch = Date.now()
  uiFeedbackState.lastValidationMessage = String(message || '')

  const selectableNodes = Array.from(
    document.querySelectorAll(
      'form input:not([type="hidden"]), form textarea, form select, .el-form input, .el-form textarea, .el-form .el-select',
    ),
  )

  if (!selectableNodes.length) {
    return
  }

  selectableNodes.forEach((nodeItem) => {
    if (nodeItem instanceof HTMLElement) {
      nodeItem.classList.add('qb-validation-highlight')
    }
  })

  const firstTarget = selectableNodes.find((nodeItem) => nodeItem instanceof HTMLElement)
  if (firstTarget instanceof HTMLElement && typeof firstTarget.focus === 'function') {
    firstTarget.focus({ preventScroll: true })
  }

  window.setTimeout(() => {
    selectableNodes.forEach((nodeItem) => {
      if (nodeItem instanceof HTMLElement) {
        nodeItem.classList.remove('qb-validation-highlight')
      }
    })
  }, 1800)
}
