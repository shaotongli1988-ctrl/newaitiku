import { computed } from 'vue'
import { useUserStore } from '../stores/userStore.js'

function normalizePermissionKeys(permissionKeys) {
  if (Array.isArray(permissionKeys)) {
    return permissionKeys
      .map((permissionKey) => String(permissionKey || '').trim())
      .filter(Boolean)
  }
  const singlePermissionKey = String(permissionKeys || '').trim()
  return singlePermissionKey ? [singlePermissionKey] : []
}

function normalizePostTag(postTag) {
  return String(postTag || '').trim()
}

export function usePermission(store) {
  const userStore = store || useUserStore()

  const hasPermission = (permissionKey) => userStore.hasPermission(permissionKey)

  const hasAllPermissions = (permissionKeys = []) => {
    const normalizedPermissionKeys = normalizePermissionKeys(permissionKeys)
    if (!normalizedPermissionKeys.length) {
      return true
    }
    return normalizedPermissionKeys.every((permissionKey) => hasPermission(permissionKey))
  }

  const hasAnyPermission = (permissionKeys = []) => {
    const normalizedPermissionKeys = normalizePermissionKeys(permissionKeys)
    if (!normalizedPermissionKeys.length) {
      return true
    }
    return normalizedPermissionKeys.some((permissionKey) => hasPermission(permissionKey))
  }

  const hasPostTag = (postTag) => {
    const normalizedPostTag = normalizePostTag(postTag)
    return normalizedPostTag ? userStore.hasPostTag(normalizedPostTag) : false
  }

  const canAccess = ({ role = '', allowedRoles = [], requiredPermissions = [] } = {}) =>
    userStore.ensureAccess({
      role,
      allowedRoles,
      requiredPermissions,
    })

  return {
    role: computed(() => String(userStore.role || '').trim()),
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasPostTag,
    canAccess,
  }
}

export default usePermission
