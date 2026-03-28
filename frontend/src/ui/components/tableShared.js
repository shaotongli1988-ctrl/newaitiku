export const tableContextKey = Symbol('ui-table')

export function normalizeTableColumnType(type) {
  const candidate = String(type || '').trim()
  if (['selection', 'index', 'expand'].includes(candidate)) {
    return candidate
  }
  return 'default'
}

export function normalizeFixedPosition(fixed) {
  if (fixed === true) {
    return 'left'
  }
  const candidate = String(fixed || '').trim().toLowerCase()
  if (candidate === 'left' || candidate === 'right') {
    return candidate
  }
  return ''
}

export function parseTableSize(value, fallback = 160) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  const candidate = String(value || '').trim()
  if (!candidate) {
    return fallback
  }

  const matched = candidate.match(/^(\d+(?:\.\d+)?)/)
  if (!matched) {
    return fallback
  }

  return Number(matched[1] || fallback)
}

export function resolveTableRowKey(row, rowKey, index = 0) {
  if (typeof rowKey === 'function') {
    return String(rowKey(row, index) ?? '')
  }

  const keyPath = String(rowKey || '').trim()
  if (!keyPath) {
    return String(index)
  }

  return String(row?.[keyPath] ?? '')
}

export function normalizeExpandedKeys(keys) {
  return Array.from(
    new Set(
      (Array.isArray(keys) ? keys : [])
        .map((item) => String(item || '').trim())
        .filter((item) => Boolean(item)),
    ),
  )
}

export function buildStickyOffsets(columns) {
  const normalizedColumns = Array.isArray(columns) ? columns : []
  const leftOffsets = {}
  const rightOffsets = {}

  let currentLeft = 0
  normalizedColumns.forEach((column) => {
    if (normalizeFixedPosition(column?.fixed) !== 'left') {
      return
    }
    leftOffsets[column.uid] = currentLeft
    currentLeft += parseTableSize(column?.width ?? column?.minWidth, column?.type === 'selection' ? 55 : 160)
  })

  let currentRight = 0
  normalizedColumns
    .slice()
    .reverse()
    .forEach((column) => {
      if (normalizeFixedPosition(column?.fixed) !== 'right') {
        return
      }
      rightOffsets[column.uid] = currentRight
      currentRight += parseTableSize(column?.width ?? column?.minWidth, 160)
    })

  return { leftOffsets, rightOffsets }
}
