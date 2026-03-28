import { defineStore } from 'pinia'
import { clearAccessToken, getAccessToken, setAccessToken } from '../api/request'

const ROLE_STORAGE_KEY = 'qbCurrentRole'
const PERMISSION_STORAGE_KEY = 'qbPermissionKeys'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getAccessToken(),
    currentRole: 'student',
    permissionKeys: [],
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    bootstrapAuth() {
      this.currentRole = localStorage.getItem(ROLE_STORAGE_KEY) || 'student'
      const rawPermissionKeys = localStorage.getItem(PERMISSION_STORAGE_KEY)
      this.permissionKeys = rawPermissionKeys ? JSON.parse(rawPermissionKeys) : []
      this.token = getAccessToken()
    },
    setToken(token) {
      this.token = token || ''

      if (this.token) {
        setAccessToken(this.token)
      } else {
        clearAccessToken()
      }
    },
    setCurrentRole(role) {
      this.currentRole = role
      localStorage.setItem(ROLE_STORAGE_KEY, role)
    },
    setPermissionKeys(permissionKeys) {
      this.permissionKeys = Array.isArray(permissionKeys) ? permissionKeys : []
      localStorage.setItem(PERMISSION_STORAGE_KEY, JSON.stringify(this.permissionKeys))
    },
    hasPermission(permissionKey) {
      return this.permissionKeys.includes(permissionKey)
    },
  },
})
