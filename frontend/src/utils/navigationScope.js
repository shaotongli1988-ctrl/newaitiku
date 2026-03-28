function normalizeEntryType(entryType = '') {
  return String(entryType || '').trim() === 'teacher' ? 'teacher' : 'student'
}

function normalizePath(path = '') {
  return String(path || '').trim()
}

export function isRoutePathAllowedInEntry(path = '', entryType = '') {
  const normalizedPath = normalizePath(path)
  const normalizedEntryType = normalizeEntryType(entryType)

  if (
    !normalizedPath
    || normalizedPath === '/'
    || normalizedPath === '/login'
    || normalizedPath === '/error/500'
    || normalizedPath === '/messages'
    || normalizedPath.startsWith('/messages/')
  ) {
    return true
  }

  if (normalizedEntryType === 'teacher') {
    return normalizedPath.startsWith('/teacher/') || normalizedPath.startsWith('/admin/')
  }

  return normalizedPath.startsWith('/student/')
}
