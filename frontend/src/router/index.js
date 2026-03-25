import { ElMessage } from '@/ui/feedback'
import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '../api/request'
import { useUserStore } from '../stores/userStore.js'
import { isRoutePathAllowedInEntry } from '../utils/navigationScope.js'
import { resolveStudentOnboardingRedirect } from '../utils/studentOnboarding.js'

function resolveEntryFallbackPath(router, entryType, homePath) {
  const normalizedHomePath = String(homePath || '').trim()
  if (normalizedHomePath && router.resolve(normalizedHomePath).matched.length > 0) {
    return normalizedHomePath
  }
  return entryType === 'teacher' ? '/teacher/home' : '/student/home'
}

function redirectToRoleHome(homePath, fallbackPath) {
  const targetPath = String(homePath || '').trim() || String(fallbackPath || '').trim()
  if (!targetPath) {
    return false
  }
  if (window.location.pathname !== targetPath) {
    window.location.assign(targetPath)
  }
  return false
}

export function createScopedRouter({ routes = [], entryType = 'student' } = {}) {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach(async (to) => {
    const userStore = useUserStore()
    const hasToken = Boolean(String(getAccessToken() || '').trim())
    if (!userStore.isHydrated && hasToken) {
      await userStore.initialize({ routePath: to.path })
    }

    if (!isRoutePathAllowedInEntry(to.path, entryType)) {
      ElMessage.warning(
        entryType === 'teacher'
          ? '当前管理入口不提供学生页面，已跳转到可访问页面。'
          : '当前学生入口不提供教师/超管页面，已跳转到学习首页。',
      )
      return resolveEntryFallbackPath(router, entryType, userStore.homePath)
    }

    const accessResult = userStore.ensureAccess({
      allowedRoles: to.meta?.allowedRoles,
      requiredPermissions: to.meta?.requiredPermissions,
    })

    if (!accessResult.allowed) {
      const normalizedRole = String(userStore.role || '').trim()
      if (entryType === 'student' && normalizedRole === 'teacher') {
        ElMessage.warning('当前入口仅面向学生，正在切换到对应管理入口。')
        return redirectToRoleHome(
          userStore.homePath,
          '/teacher/home',
        )
      }
      if (entryType === 'teacher' && normalizedRole === 'student') {
        ElMessage.warning('当前入口仅面向教师/超管，正在切换到学生入口。')
        return redirectToRoleHome(userStore.homePath, '/student/home')
      }

      ElMessage.warning(
        accessResult.reason === 'permission'
          ? '当前账号缺少页面权限，已跳转到可访问页面。'
          : '当前角色无权进入该分区，已跳转到可访问页面。',
      )
      return resolveEntryFallbackPath(router, entryType, userStore.homePath)
    }

    const onboardingRedirectPath = resolveStudentOnboardingRedirect({
      role: userStore.role,
      path: to.path,
      userId: userStore.userId,
    })
    if (onboardingRedirectPath) {
      return {
        path: onboardingRedirectPath,
        query: {
          ...(to.fullPath ? { redirect: to.fullPath } : {}),
        },
      }
    }

    return true
  })

  router.afterEach((to) => {
    const pageTitle = typeof to.meta?.title === 'string' ? to.meta.title : '专升本题库系统'
    document.title = `${pageTitle} - 专升本题库系统`
  })

  return router
}
