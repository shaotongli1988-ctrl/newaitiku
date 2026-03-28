const DEV_LOGIN_PRESETS = {
  admin: {
    role: 'super_admin',
    phone: '13800000001',
    password: import.meta.env.VITE_DEV_LOGIN_ADMIN_PASSWORD || 'seed-password-admin-001',
    homePath: '/admin/home',
  },
  teacher: {
    role: 'teacher',
    phone: '13800000002',
    password: import.meta.env.VITE_DEV_LOGIN_TEACHER_PASSWORD || 'seed-password-teacher-001',
    homePath: '/teacher/home',
  },
  student: {
    role: 'student',
    phone: '13800000005',
    password: import.meta.env.VITE_DEV_LOGIN_STUDENT_PASSWORD || 'seed-password-student-001',
    homePath: '/student/home',
  },
}

export function resolveDevLoginPreset(rawPreset) {
  const normalizedPreset = String(rawPreset || '').trim().toLowerCase()
  if (!normalizedPreset) {
    return null
  }
  return DEV_LOGIN_PRESETS[normalizedPreset] || null
}

export function resolveDevLoginPresetFromLocation(search = '') {
  const params = new URLSearchParams(String(search || ''))
  return resolveDevLoginPreset(params.get('devLogin'))
}

export function resolveDevLoginPresetFromPath(pathname = '') {
  const normalizedPathname = String(pathname || '').trim()
  if (normalizedPathname === '/student' || normalizedPathname.startsWith('/student/')) {
    return DEV_LOGIN_PRESETS.student
  }
  if (
    normalizedPathname === '/teacher'
    || normalizedPathname === '/admin'
    || normalizedPathname.startsWith('/teacher/')
    || normalizedPathname.startsWith('/admin/')
  ) {
    return DEV_LOGIN_PRESETS.teacher
  }
  return null
}

export function resolveBootstrapPathname({
  pathname = '',
  homePath = '',
  devLoginPreset = null,
} = {}) {
  const normalizedPathname = String(pathname || '').trim()
  const normalizedHomePath = String(homePath || '').trim()
  const presetHomePath = String(devLoginPreset?.homePath || '').trim()

  if (normalizedPathname === '/' || normalizedPathname === '/login') {
    if (presetHomePath) {
      return presetHomePath
    }
    if (normalizedHomePath) {
      return normalizedHomePath
    }
  }

  return normalizedPathname || '/'
}

export function buildNormalizedBootstrapUrl({
  pathname = '',
  search = '',
  hash = '',
} = {}) {
  const params = new URLSearchParams(String(search || ''))
  params.delete('devLogin')
  const normalizedSearch = params.toString()
  return `${String(pathname || '').trim() || '/'}${normalizedSearch ? `?${normalizedSearch}` : ''}${String(hash || '').trim()}`
}
