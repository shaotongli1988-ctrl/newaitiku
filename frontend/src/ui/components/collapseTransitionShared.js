export function normalizeCollapseDuration(duration, fallback = 220) {
  const numericDuration = Number(duration)
  if (!Number.isFinite(numericDuration) || numericDuration < 0) {
    return fallback
  }
  return numericDuration
}
