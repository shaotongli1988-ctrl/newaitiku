import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '../style/main.css'
import App from '../App.vue'
import createLoadingDirective from '../directives/loading.js'
import createPermissionDirective from '../directives/permission.js'
import { clearAccessToken, getAccessToken, sanitizeIdentityClientState } from '../api/request'
import { useUserStore } from '../stores/userStore.js'
import {
  buildNormalizedBootstrapUrl,
  resolveBootstrapPathname,
  resolveDevLoginPresetFromPath,
  resolveDevLoginPresetFromLocation,
} from '../utils/devLogin.js'

function resetDevLoginClientState() {
  if (typeof localStorage === 'undefined') {
    return
  }

  const keysToRemove = []
  for (let index = 0; index < localStorage.length; index += 1) {
    const storageKey = String(localStorage.key(index) || '').trim()
    if (storageKey.startsWith('qb')) {
      keysToRemove.push(storageKey)
    }
  }

  keysToRemove.forEach((storageKey) => {
    localStorage.removeItem(storageKey)
  })
  clearAccessToken()
  window.__QB_ASSIGNED_JOINT_GROUP__ = ''
}

export async function bootstrapWithRouter(router, { entryType = '' } = {}) {
  sanitizeIdentityClientState()
  window.__QB_ENTRY_TYPE__ = String(entryType || '').trim()
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)

  const userStore = useUserStore(pinia)
  const normalizedEntryType = String(entryType || '').trim()
  const explicitDevLoginPreset = import.meta.env.DEV
    ? resolveDevLoginPresetFromLocation(window.location.search)
    : null
  const routeDrivenDevLoginPreset = import.meta.env.DEV && !getAccessToken() && !explicitDevLoginPreset
    ? resolveDevLoginPresetFromPath(window.location.pathname)
    : null
  const devLoginPreset = explicitDevLoginPreset || routeDrivenDevLoginPreset

  if (devLoginPreset) {
    resetDevLoginClientState()
    await userStore.login({
      phone: devLoginPreset.phone,
      password: devLoginPreset.password,
    })
  }

  const hasToken = Boolean(String(getAccessToken() || '').trim())
  const bootstrapPath = resolveBootstrapPathname({
    pathname: window.location.pathname,
    homePath: userStore.homePath,
    devLoginPreset,
  })
  const normalizedBootstrapUrl = buildNormalizedBootstrapUrl({
    pathname: bootstrapPath,
    search: window.location.search,
    hash: window.location.hash,
  })

  if (normalizedBootstrapUrl !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
    window.history.replaceState({}, '', normalizedBootstrapUrl)
  }

  await userStore.initialize({
    routePath: bootstrapPath,
    entryType: normalizedEntryType,
    force: userStore.initialized && window.location.pathname !== bootstrapPath,
  })

  app.use(router)
  app.directive('loading', createLoadingDirective())
  app.directive('permission', createPermissionDirective(pinia))
  app.mount('#app')
}
