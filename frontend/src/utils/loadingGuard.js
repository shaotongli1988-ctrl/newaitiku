function normalizeLoadingRefs(loadingRefOrRefs) {
  const loadingRefs = Array.isArray(loadingRefOrRefs) ? loadingRefOrRefs : [loadingRefOrRefs]
  if (!loadingRefs.length || loadingRefs.some((loadingRef) => !loadingRef || typeof loadingRef !== 'object')) {
    throw new Error('loadingRef is required')
  }
  return loadingRefs
}

export async function runWithLoadingGuard(loadingRefOrRefs, task) {
  const loadingRefs = normalizeLoadingRefs(loadingRefOrRefs)
  if (typeof task !== 'function') {
    throw new Error('task must be a function')
  }
  if (loadingRefs.some((loadingRef) => loadingRef.value)) {
    return false
  }

  loadingRefs.forEach((loadingRef) => {
    loadingRef.value = true
  })
  try {
    await task()
    return true
  } finally {
    loadingRefs.forEach((loadingRef) => {
      loadingRef.value = false
    })
  }
}
