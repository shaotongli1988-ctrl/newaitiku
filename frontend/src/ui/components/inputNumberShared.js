export function toFiniteNumber(value) {
  if (value === '' || value === null || value === undefined) {
    return undefined
  }

  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : undefined
}

export function resolveInputNumberPrecision(step = 1, precision = undefined) {
  if (Number.isInteger(precision) && precision >= 0) {
    return precision
  }

  const stepText = String(step ?? '')
  const dotIndex = stepText.indexOf('.')
  return dotIndex >= 0 ? stepText.length - dotIndex - 1 : 0
}

export function roundInputNumber(value, precision = 0) {
  const numericValue = toFiniteNumber(value)
  if (numericValue === undefined) {
    return undefined
  }

  if (!Number.isInteger(precision) || precision < 0) {
    return numericValue
  }

  const factor = 10 ** precision
  return Math.round((numericValue + Number.EPSILON) * factor) / factor
}

export function clampInputNumber(value, min = undefined, max = undefined) {
  const numericValue = toFiniteNumber(value)
  if (numericValue === undefined) {
    return undefined
  }

  const minValue = toFiniteNumber(min)
  const maxValue = toFiniteNumber(max)

  let nextValue = numericValue
  if (minValue !== undefined) {
    nextValue = Math.max(nextValue, minValue)
  }
  if (maxValue !== undefined) {
    nextValue = Math.min(nextValue, maxValue)
  }
  return nextValue
}

export function normalizeInputNumberValue(
  value,
  { min = undefined, max = undefined, precision = undefined } = {},
) {
  const numericValue = toFiniteNumber(value)
  if (numericValue === undefined) {
    return undefined
  }

  const clampedValue = clampInputNumber(numericValue, min, max)
  return roundInputNumber(clampedValue, precision)
}

export function stepInputNumber(
  value,
  direction,
  { min = undefined, max = undefined, step = 1, precision = undefined } = {},
) {
  const stepValue = Math.abs(toFiniteNumber(step) ?? 1)
  const baseValue = toFiniteNumber(value) ?? toFiniteNumber(min) ?? 0
  const effectivePrecision = resolveInputNumberPrecision(stepValue, precision)
  const nextValue = baseValue + stepValue * (direction >= 0 ? 1 : -1)

  return normalizeInputNumberValue(nextValue, {
    min,
    max,
    precision: effectivePrecision,
  })
}

export function formatInputNumberValue(value, precision = undefined) {
  const numericValue = toFiniteNumber(value)
  if (numericValue === undefined) {
    return ''
  }

  const roundedValue = roundInputNumber(numericValue, precision)
  if (roundedValue === undefined) {
    return ''
  }

  const fixedValue = Number.isInteger(precision) && precision >= 0
    ? roundedValue.toFixed(precision)
    : String(roundedValue)

  return fixedValue.replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1')
}
