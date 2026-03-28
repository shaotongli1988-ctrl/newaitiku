export const selectContextKey = Symbol('uiSelect')

export function normalizeSelectValue(value, { multiple = false } = {}) {
  if (multiple) {
    return Array.isArray(value) ? value : []
  }
  return value
}

export function isSelectValueEmpty(value, { multiple = false } = {}) {
  if (multiple) {
    return !Array.isArray(value) || value.length === 0
  }

  return value === '' || value === null || value === undefined
}

export function toggleSelectMultipleValue(currentValue, nextValue) {
  const source = Array.isArray(currentValue) ? [...currentValue] : []
  const existingIndex = source.findIndex((item) => item === nextValue)

  if (existingIndex >= 0) {
    source.splice(existingIndex, 1)
    return source
  }

  source.push(nextValue)
  return source
}

export function filterSelectOptions(options, keyword) {
  const normalizedKeyword = String(keyword ?? '').trim().toLowerCase()
  if (!normalizedKeyword) {
    return options
  }

  return options.filter((option) => {
    const label = String(option?.label ?? '').toLowerCase()
    const value = String(option?.value ?? '').toLowerCase()
    return label.includes(normalizedKeyword) || value.includes(normalizedKeyword)
  })
}

export function findSelectOption(options, value) {
  return options.find((option) => option?.value === value)
}

export function isSelectValueEqual(left, right, { multiple = false } = {}) {
  if (!multiple) {
    return left === right
  }

  const leftItems = Array.isArray(left) ? left : []
  const rightItems = Array.isArray(right) ? right : []

  if (leftItems.length !== rightItems.length) {
    return false
  }

  return leftItems.every((item, index) => item === rightItems[index])
}
