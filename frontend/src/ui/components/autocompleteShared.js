export function normalizeAutocompleteItems(items) {
  return Array.isArray(items) ? items.filter(Boolean) : []
}

export function resolveAutocompleteItemLabel(item, valueKey = 'value') {
  if (!item || typeof item !== 'object') {
    return ''
  }

  const preferredValue = item?.[valueKey]
  if (preferredValue !== undefined && preferredValue !== null && preferredValue !== '') {
    return String(preferredValue)
  }

  if (item.value !== undefined && item.value !== null) {
    return String(item.value)
  }

  return ''
}

export async function runAutocompleteFetcher(fetchSuggestions, queryString) {
  if (typeof fetchSuggestions !== 'function') {
    return []
  }

  return await new Promise((resolve) => {
    let settled = false
    const finish = (items) => {
      if (settled) {
        return
      }
      settled = true
      resolve(normalizeAutocompleteItems(items))
    }

    const maybeResult = fetchSuggestions(queryString, finish)
    if (Array.isArray(maybeResult)) {
      finish(maybeResult)
      return
    }

    if (maybeResult && typeof maybeResult.then === 'function') {
      maybeResult.then(finish).catch(() => finish([]))
      return
    }

    if (fetchSuggestions.length < 2) {
      finish(maybeResult)
    }
  })
}
