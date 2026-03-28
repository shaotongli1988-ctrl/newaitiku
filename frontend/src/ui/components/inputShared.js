export function normalizeInputValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

export function shouldShowInputClear({
  clearable = false,
  disabled = false,
  readonly = false,
  hasValue = false,
} = {}) {
  return Boolean(clearable && !disabled && !readonly && hasValue)
}

export function resolveInputControlType(type = 'text', allowPasswordToggle = false, passwordVisible = false) {
  const candidate = String(type || 'text').trim()
  if (candidate === 'textarea') {
    return 'textarea'
  }
  if (candidate === 'password') {
    return allowPasswordToggle && passwordVisible ? 'text' : 'password'
  }
  return candidate || 'text'
}

export function resolveInputMaxlength(value) {
  if (value === '' || value === null || value === undefined) {
    return undefined
  }
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue) || numericValue <= 0) {
    return undefined
  }
  return Math.floor(numericValue)
}
