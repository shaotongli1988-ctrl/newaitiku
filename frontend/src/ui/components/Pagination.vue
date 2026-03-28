<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  total: {
    type: Number,
    default: 0,
  },
  pageSize: {
    type: Number,
    default: 10,
  },
  currentPage: {
    type: Number,
    default: 1,
  },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 30, 40, 50],
  },
  layout: {
    type: String,
    default: 'prev, pager, next',
  },
  background: {
    type: Boolean,
    default: false,
  },
  small: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:currentPage',
  'update:pageSize',
  'current-change',
  'size-change',
  'change',
])

function normalizePositiveInteger(value, fallback) {
  const candidate = Number(value)
  if (!Number.isFinite(candidate) || candidate <= 0) {
    return fallback
  }
  return Math.max(1, Math.floor(candidate))
}

const normalizedTotal = computed(() => Math.max(0, Number(props.total || 0)))
const normalizedPageSize = computed(() => normalizePositiveInteger(props.pageSize, 10))
const pageCount = computed(() => Math.max(1, Math.ceil(normalizedTotal.value / normalizedPageSize.value)))
const normalizedCurrentPage = computed(() => {
  const candidate = normalizePositiveInteger(props.currentPage, 1)
  return Math.min(candidate, pageCount.value)
})

const normalizedPageSizes = computed(() => {
  const rawItems = Array.isArray(props.pageSizes) ? props.pageSizes : []
  const uniqueItems = Array.from(new Set(rawItems.map((item) => normalizePositiveInteger(item, 10))))
  return uniqueItems.length ? uniqueItems : [10, 20, 50, 100]
})

const layoutParts = computed(() =>
  String(props.layout || 'prev, pager, next')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
)

const jumperValue = ref(String(normalizedCurrentPage.value))

watch(
  normalizedCurrentPage,
  (value) => {
    jumperValue.value = String(value)
  },
  { immediate: true },
)

const shouldRender = (part) => layoutParts.value.includes(part)

function emitPageChange(nextPage) {
  const resolvedPage = Math.min(pageCount.value, Math.max(1, normalizePositiveInteger(nextPage, normalizedCurrentPage.value)))
  if (resolvedPage === normalizedCurrentPage.value) {
    return
  }
  emit('update:currentPage', resolvedPage)
  emit('current-change', resolvedPage)
  emit('change', resolvedPage)
}

function emitPageSizeChange(nextSize) {
  const resolvedSize = normalizePositiveInteger(nextSize, normalizedPageSize.value)
  if (resolvedSize === normalizedPageSize.value) {
    return
  }
  emit('update:pageSize', resolvedSize)
  emit('size-change', resolvedSize)
}

function handlePageSizeChange(event) {
  emitPageSizeChange(event?.target?.value)
}

function handleJumperCommit() {
  emitPageChange(jumperValue.value)
  jumperValue.value = String(normalizedCurrentPage.value)
}

function buildPagerItems() {
  const totalPages = pageCount.value
  const current = normalizedCurrentPage.value

  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }

  const pages = new Set([1, totalPages, current - 1, current, current + 1])
  if (current <= 3) {
    pages.add(2)
    pages.add(3)
    pages.add(4)
  }
  if (current >= totalPages - 2) {
    pages.add(totalPages - 1)
    pages.add(totalPages - 2)
    pages.add(totalPages - 3)
  }

  const sortedPages = Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right)

  const items = []
  for (let index = 0; index < sortedPages.length; index += 1) {
    const page = sortedPages[index]
    const previous = sortedPages[index - 1]
    if (index > 0 && page - previous > 1) {
      items.push(`ellipsis-${previous}-${page}`)
    }
    items.push(page)
  }
  return items
}

const pagerItems = computed(buildPagerItems)

const paginationClasses = computed(() => [
  'ui-pagination',
  'el-pagination',
  props.background ? 'is-background' : '',
  props.small ? 'el-pagination--small' : '',
  props.disabled ? 'is-disabled' : '',
])

function isEllipsis(item) {
  return typeof item === 'string' && item.startsWith('ellipsis-')
}
</script>

<template>
  <nav :class="paginationClasses" aria-label="Pagination">
    <span v-if="shouldRender('total')" class="el-pagination__total">
      共 {{ normalizedTotal }} 条
    </span>

    <label v-if="shouldRender('sizes')" class="el-pagination__sizes">
      <span class="el-pagination__sizes-label">每页</span>
      <select
        class="el-select__wrapper"
        :value="String(normalizedPageSize)"
        :disabled="disabled"
        @change="handlePageSizeChange"
      >
        <option v-for="size in normalizedPageSizes" :key="size" :value="String(size)">
          {{ size }} 条/页
        </option>
      </select>
    </label>

    <button
      v-if="shouldRender('prev')"
      type="button"
      class="btn-prev"
      :disabled="disabled || normalizedCurrentPage <= 1"
      @click="emitPageChange(normalizedCurrentPage - 1)"
    >
      上一页
    </button>

    <ul v-if="shouldRender('pager')" class="el-pager">
      <li
        v-for="item in pagerItems"
        :key="item"
        class="number"
        :class="{
          'is-active': item === normalizedCurrentPage,
          'is-disabled': isEllipsis(item) || disabled,
          'is-more': isEllipsis(item),
        }"
      >
        <span v-if="isEllipsis(item)">...</span>
        <button
          v-else
          type="button"
          class="number-button"
          :disabled="disabled"
          @click="emitPageChange(item)"
        >
          {{ item }}
        </button>
      </li>
    </ul>

    <button
      v-if="shouldRender('next')"
      type="button"
      class="btn-next"
      :disabled="disabled || normalizedCurrentPage >= pageCount"
      @click="emitPageChange(normalizedCurrentPage + 1)"
    >
      下一页
    </button>

    <label v-if="shouldRender('jumper')" class="el-pagination__jump">
      前往
      <input
        v-model="jumperValue"
        class="el-pagination__editor"
        inputmode="numeric"
        :disabled="disabled"
        @keydown.enter.prevent="handleJumperCommit"
        @blur="handleJumperCommit"
      >
      页
    </label>
  </nav>
</template>

<style scoped>
.ui-pagination {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.ui-pagination.is-disabled {
  opacity: 0.72;
}

.el-pagination__total,
.el-pagination__jump,
.el-pagination__sizes {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.el-pagination__sizes-label {
  color: var(--qb-text-subtle-7);
}

.el-select__wrapper,
.el-pagination__editor {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 10px;
  background: var(--qb-surface-strong);
  color: var(--qb-text-primary);
  font: inherit;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.el-select__wrapper:focus,
.el-pagination__editor:focus {
  outline: none;
  border-color: color-mix(in srgb, var(--qb-primary-student) 56%, white 44%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
}

.el-select__wrapper {
  min-width: 112px;
}

.el-pagination__editor {
  width: 64px;
  text-align: center;
}

.btn-prev,
.btn-next,
.number-button {
  min-width: 34px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
  transition: border-color 180ms ease, background-color 180ms ease, color 180ms ease, opacity 180ms ease;
}

.el-pager {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.number {
  display: inline-flex;
}

.number-button {
  justify-content: center;
}

.btn-prev:hover:not(:disabled),
.btn-next:hover:not(:disabled),
.number-button:hover:not(:disabled) {
  border-color: var(--qb-border-soft);
  background: color-mix(in srgb, var(--qb-bg-muted) 84%, white 16%);
  color: var(--qb-text-primary);
}

.number.is-active .number-button {
  border-color: color-mix(in srgb, var(--qb-primary-student) 44%, white 56%);
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 82%, white 18%);
  color: var(--qb-primary-student);
  font-weight: 700;
}

.number.is-more {
  min-width: 34px;
  min-height: 34px;
  align-items: center;
  justify-content: center;
  color: var(--qb-text-subtle-6);
}

.btn-prev:disabled,
.btn-next:disabled,
.number-button:disabled,
.el-select__wrapper:disabled,
.el-pagination__editor:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.ui-pagination.is-background .btn-prev,
.ui-pagination.is-background .btn-next,
.ui-pagination.is-background .number-button,
.ui-pagination.is-background .number.is-more {
  border-color: var(--qb-border-soft);
  background: var(--qb-surface-strong);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.36);
}

.ui-pagination.is-background .number.is-active .number-button {
  background: var(--qb-primary-student);
  border-color: transparent;
  color: var(--qb-text-inverse);
}

.ui-pagination.el-pagination--small {
  gap: 8px;
  font-size: 12px;
}

.ui-pagination.el-pagination--small .btn-prev,
.ui-pagination.el-pagination--small .btn-next,
.ui-pagination.el-pagination--small .number-button,
.ui-pagination.el-pagination--small .number.is-more,
.ui-pagination.el-pagination--small .el-select__wrapper,
.ui-pagination.el-pagination--small .el-pagination__editor {
  min-height: 30px;
  min-width: 30px;
  border-radius: 8px;
}
</style>
