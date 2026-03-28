export function resolveEntryTypeFromRole(role = '') {
  const normalizedRole = String(role || '').trim()
  if (normalizedRole === 'teacher' || normalizedRole === 'super_admin') {
    return 'teacher'
  }
  return 'student'
}

export function resolveEntryTypeFromLocation(pathname = '', storedRole = '', actorRole = '') {
  const normalizedPathname = String(pathname || '').trim()

  if (
    normalizedPathname === '/teacher'
    || normalizedPathname === '/admin'
    || normalizedPathname.startsWith('/teacher/')
    || normalizedPathname.startsWith('/admin/')
  ) {
    return 'teacher'
  }

  if (normalizedPathname === '/student' || normalizedPathname.startsWith('/student/')) {
    return 'student'
  }

  const normalizedActorRole = String(actorRole || '').trim()
  if (normalizedActorRole) {
    return resolveEntryTypeFromRole(normalizedActorRole)
  }

  return resolveEntryTypeFromRole(storedRole)
}
