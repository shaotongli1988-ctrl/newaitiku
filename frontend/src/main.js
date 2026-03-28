import studentRouter from './router/student'
import teacherRouter from './router/teacher'
import { fetchManagementProfile } from './api/auth'
import { getAccessToken } from './api/request'
import { bootstrapWithRouter } from './entries/bootstrap'
import { resolveEntryTypeFromLocation, resolveEntryTypeFromRole } from './utils/entryType'
import { resolveDevLoginPresetFromLocation, resolveDevLoginPresetFromPath } from './utils/devLogin'

async function resolveRuntimeEntryType() {
  const pathname = window.location.pathname
  const storedRole = localStorage.getItem('qbUserRole') || ''
  const hasToken = Boolean(String(getAccessToken() || '').trim())
  let actorRole = ''
  const explicitDevLoginPreset = import.meta.env.DEV
    ? resolveDevLoginPresetFromLocation(window.location.search)
    : null
  const routeDrivenDevLoginPreset = import.meta.env.DEV && !hasToken && !explicitDevLoginPreset
    ? resolveDevLoginPresetFromPath(pathname)
    : null
  const devLoginPreset = explicitDevLoginPreset || routeDrivenDevLoginPreset

  if (
    hasToken
    && !pathname.startsWith('/student/')
    && !pathname.startsWith('/teacher/')
    && !pathname.startsWith('/admin/')
  ) {
    try {
      const response = await fetchManagementProfile()
      const payload = response?.data && typeof response.data === 'object' ? response.data : response
      actorRole = String(payload?.data?.role || payload?.role || '').trim()
    } catch (error) {
      actorRole = ''
    }
  }

  if (!pathname.startsWith('/student/') && !pathname.startsWith('/teacher/') && !pathname.startsWith('/admin/') && devLoginPreset?.role) {
    return resolveEntryTypeFromRole(devLoginPreset.role)
  }

  return resolveEntryTypeFromLocation(pathname, storedRole, actorRole)
}

async function bootstrap() {
  const entryType = await resolveRuntimeEntryType()
  const router = entryType === 'teacher' ? teacherRouter : studentRouter

  await bootstrapWithRouter(router, { entryType })
}

bootstrap()
