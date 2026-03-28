import { effectScope, watch } from 'vue'
import { useUserStore } from '../stores/userStore.js'

const PERMISSION_CONTEXT_KEY = Symbol('permissionDirectiveContext')

/**
 * 解析指令值，统一为可判断的权限模型。
 * 支持：
 * 1) 字符串：`v-permission="'question:manage'"`
 * 2) 数组：`v-permission="['question:manage', 'paper:manage']"`（默认 all）
 * 3) 对象：`v-permission="{ anyOf: ['settings:manage', 'student:manage'] }"`
 */
function normalizePermissionExpression(value) {
  if (typeof value === 'string') {
    return { mode: 'all', keys: [value] }
  }

  if (Array.isArray(value)) {
    return { mode: 'all', keys: value }
  }

  if (value && typeof value === 'object') {
    if (Array.isArray(value.anyOf)) {
      return { mode: 'any', keys: value.anyOf }
    }
    if (Array.isArray(value.allOf)) {
      return { mode: 'all', keys: value.allOf }
    }
  }

  return { mode: 'all', keys: [] }
}

/**
 * 真正的权限判定函数：
 * - all 模式要求全部权限命中；
 * - any 模式命中任一权限即可。
 */
function evaluatePermission(userStore, value, modifiers) {
  const parsedExpression = normalizePermissionExpression(value)
  const explicitMode = modifiers.any ? 'any' : modifiers.all ? 'all' : parsedExpression.mode
  const normalizedKeys = parsedExpression.keys
    .map((permissionKey) => String(permissionKey || '').trim())
    .filter(Boolean)

  if (!normalizedKeys.length) {
    return true
  }

  if (explicitMode === 'any') {
    return normalizedKeys.some((permissionKey) => userStore.hasPermission(permissionKey))
  }

  return normalizedKeys.every((permissionKey) => userStore.hasPermission(permissionKey))
}

/**
 * 使用注释锚点替换元素，确保无权限时不渲染目标 DOM。
 */
function unmountElement(el, context) {
  if (context.anchorNode || !el.parentNode) {
    return
  }
  const anchorNode = document.createComment('v-permission-anchor')
  el.parentNode.replaceChild(anchorNode, el)
  context.anchorNode = anchorNode
}

/**
 * 权限恢复时，把真实元素重新挂载回原位置。
 */
function mountElement(el, context) {
  if (!context.anchorNode || !context.anchorNode.parentNode) {
    return
  }
  context.anchorNode.parentNode.replaceChild(el, context.anchorNode)
  context.anchorNode = null
}

function applyPermissionRender(el, binding, userStore) {
  const context = el[PERMISSION_CONTEXT_KEY]
  if (!context) {
    return
  }
  const hasAccess = evaluatePermission(userStore, binding.value, binding.modifiers || {})
  if (hasAccess) {
    mountElement(el, context)
  } else {
    unmountElement(el, context)
  }
}

/**
 * 创建全局 `v-permission` 指令，统一接入 Pinia 的 userStore。
 */
export function createPermissionDirective(pinia) {
  const userStore = useUserStore(pinia)

  return {
    mounted(el, binding) {
      const scope = effectScope()
      el[PERMISSION_CONTEXT_KEY] = {
        anchorNode: null,
        scope,
      }

      scope.run(() => {
        watch(
          () => userStore.permissions.slice(),
          () => {
            applyPermissionRender(el, binding, userStore)
          },
          { immediate: true },
        )
      })
    },

    updated(el, binding) {
      applyPermissionRender(el, binding, userStore)
    },

    unmounted(el) {
      const context = el[PERMISSION_CONTEXT_KEY]
      if (!context) {
        return
      }
      context.scope.stop()
      if (context.anchorNode?.parentNode) {
        context.anchorNode.parentNode.removeChild(context.anchorNode)
      }
      delete el[PERMISSION_CONTEXT_KEY]
    },
  }
}

export default createPermissionDirective
