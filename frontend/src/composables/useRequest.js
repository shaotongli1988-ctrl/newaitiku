import { ref } from 'vue'

export function useRequest(task, options = {}) {
  const loading = ref(false)
  const error = ref(null)

  async function run(...args) {
    loading.value = true
    error.value = null
    try {
      const result = await task(...args)
      if (typeof options.onSuccess === 'function') {
        await options.onSuccess(result, ...args)
      }
      return result
    } catch (requestError) {
      error.value = requestError
      if (typeof options.onError === 'function') {
        await options.onError(requestError, ...args)
      } else {
        throw requestError
      }
      return null
    } finally {
      loading.value = false
      if (typeof options.onFinally === 'function') {
        await options.onFinally(...args)
      }
    }
  }

  return {
    loading,
    error,
    run,
  }
}
