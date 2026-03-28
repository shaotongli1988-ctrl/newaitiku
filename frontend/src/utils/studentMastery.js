function toText(value) {
  return String(value || '').trim()
}

export function normalizeMasteryScore(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  const normalized = numericValue > 1 ? numericValue / 100 : numericValue
  return Math.max(0, Math.min(1, normalized)) * 100
}

export function computeSubjectMastery(row) {
  const accuracy = normalizeMasteryScore(row?.accuracy)
  const speed = normalizeMasteryScore(row?.speed)
  const frequency = normalizeMasteryScore(row?.frequency)
  return Math.round((accuracy * 0.6) + (speed * 0.2) + (frequency * 0.2))
}

export function buildSubjectMetaById(subjectRows = []) {
  return Object.fromEntries(
    (Array.isArray(subjectRows) ? subjectRows : [])
      .map((item) => {
        const subjectId = toText(item?.subjectId)
        if (!subjectId) {
          return null
        }
        return [
          subjectId,
          {
            subjectCode: toText(item?.subjectCode),
            subjectName: toText(item?.subjectName) || toText(item?.subjectCode) || subjectId,
          },
        ]
      })
      .filter(Boolean),
  )
}

export function normalizeSubjectCode(subjectCode, fallbackLabel, index = 0) {
  const raw = toText(subjectCode) || toText(fallbackLabel) || `subject_${index + 1}`
  return raw
    .replace(/^subject[-_]?/i, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase()
}

export function resolveSubjectDimensionLabel(subjectId, subjectMetaMap = {}, index = 0) {
  const subjectMeta = subjectMetaMap[toText(subjectId)]
  if (subjectMeta?.subjectName) {
    return subjectMeta.subjectName
  }

  const normalized = toText(subjectId)
  if (!normalized) {
    return `科目 ${index + 1}`
  }

  return normalized
    .replace(/^subject[-_]?/i, '')
    .replace(/[_-]+/g, ' ')
    .trim()
    || `科目 ${index + 1}`
}

export function buildRadarDimensions(rows = [], subjectMetaMap = {}) {
  return (Array.isArray(rows) ? rows : []).map((row, index) => {
    const normalizedSubjectId = toText(row?.subjectId)
    const subjectMeta = subjectMetaMap[normalizedSubjectId] || {}
    const label = resolveSubjectDimensionLabel(normalizedSubjectId, subjectMetaMap, index)
    return {
      label,
      subjectCode: normalizeSubjectCode(subjectMeta.subjectCode || row?.subjectCode || normalizedSubjectId, label, index),
      mastery: computeSubjectMastery(row),
      accuracy: Math.round(normalizeMasteryScore(row?.accuracy)),
      speed: Math.round(normalizeMasteryScore(row?.speed)),
      frequency: Math.round(normalizeMasteryScore(row?.frequency)),
    }
  })
}
