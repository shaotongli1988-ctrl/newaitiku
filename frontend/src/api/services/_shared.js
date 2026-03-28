// Observability note: shared API serializers stay aligned with log/trace/metric naming used by delivery guards.
export function assertRequired(value, fieldName) {
  if (value === undefined || value === null || String(value).trim() === '') {
    throw new Error(`${fieldName} is required`)
  }
}

export function encodePath(value) {
  return encodeURIComponent(String(value))
}

export function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

export function unwrapPageData(response) {
  const data = unwrapData(response) || {}
  return {
    items: Array.isArray(data.items) ? data.items : [],
    page: Number(data.page || 1),
    size: Number(data.size || 10),
    total: Number(data.total || 0),
  }
}

export function normalizeString(value) {
  return String(value || '').trim()
}
