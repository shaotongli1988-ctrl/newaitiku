export function clampSliderValue(value, min = 0, max = 100) {
  const numericValue = Number(value)
  const lowerBound = Number(min)
  const upperBound = Number(max)
  if (!Number.isFinite(numericValue)) {
    return lowerBound
  }
  return Math.min(upperBound, Math.max(lowerBound, numericValue))
}

export function normalizeSliderStep(step) {
  const numericStep = Number(step)
  return Number.isFinite(numericStep) && numericStep > 0 ? numericStep : 1
}

export function normalizeSliderValue(value, { min = 0, max = 100, step = 1 } = {}) {
  const clampedValue = clampSliderValue(value, min, max)
  const safeStep = normalizeSliderStep(step)
  const lowerBound = Number(min)
  const steppedValue = Math.round((clampedValue - lowerBound) / safeStep) * safeStep + lowerBound
  return clampSliderValue(Number(steppedValue.toFixed(6)), min, max)
}

export function resolveSliderFillPercent(value, min = 0, max = 100) {
  const lowerBound = Number(min)
  const upperBound = Number(max)
  if (upperBound <= lowerBound) {
    return 0
  }

  return ((clampSliderValue(value, min, max) - lowerBound) / (upperBound - lowerBound)) * 100
}
