import { reactive, ref } from 'vue'

export function useTable({ createInitialFilters, createInitialPagination, fetchPage, onLoaded, onError }) {
  const rows = ref([])
  const loading = ref(false)
  const filters = reactive(createInitialFilters())
  const pagination = reactive(createInitialPagination())

  async function loadRows() {
    loading.value = true
    try {
      const pageData = await fetchPage({ filters, pagination })
      rows.value = Array.isArray(pageData?.items) ? pageData.items : []
      pagination.total = Number(pageData?.total || 0)
      if (typeof onLoaded === 'function') {
        await onLoaded(rows.value, pageData)
      }
      return pageData
    } catch (error) {
      rows.value = []
      pagination.total = 0
      if (typeof onError === 'function') {
        await onError(error)
      } else {
        throw error
      }
      return null
    } finally {
      loading.value = false
    }
  }

  function resetFilters(nextState = {}) {
    Object.assign(filters, createInitialFilters(), nextState)
  }

  function handleSearch() {
    pagination.page = 1
    return loadRows()
  }

  function handleReset(nextState = {}) {
    resetFilters(nextState)
    pagination.page = 1
    return loadRows()
  }

  function handlePageChange(nextPage) {
    pagination.page = Number(nextPage || 1)
    return loadRows()
  }

  function handlePageSizeChange(nextSize) {
    pagination.size = Number(nextSize || createInitialPagination().size || 20)
    pagination.page = 1
    return loadRows()
  }

  return {
    rows,
    loading,
    filters,
    pagination,
    loadRows,
    resetFilters,
    handleSearch,
    handleReset,
    handlePageChange,
    handlePageSizeChange,
  }
}
