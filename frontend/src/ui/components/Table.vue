<script setup>
import {
  computed,
  defineComponent,
  h,
  nextTick,
  onBeforeUnmount,
  onMounted,
  provide,
  reactive,
  ref,
  useAttrs,
  watch,
} from 'vue'
import {
  buildStickyOffsets,
  normalizeExpandedKeys,
  normalizeFixedPosition,
  normalizeTableColumnType,
  parseTableSize,
  resolveTableRowKey,
  tableContextKey,
} from './tableShared'

defineOptions({
  inheritAttrs: false,
})

const SlotRenderer = defineComponent({
  name: 'UiTableSlotRenderer',
  props: {
    render: {
      type: Function,
      default: null,
    },
    scope: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    return () => props.render?.(props.scope) || null
  },
})

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: [String, Function],
    default: '',
  },
  border: {
    type: Boolean,
    default: false,
  },
  stripe: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: '',
  },
  emptyText: {
    type: String,
    default: '暂无数据',
  },
  maxHeight: {
    type: [String, Number],
    default: undefined,
  },
  expandRowKeys: {
    type: Array,
    default: undefined,
  },
})

const emit = defineEmits(['selection-change', 'expand-change'])
const attrs = useAttrs()
const columnsMap = reactive(new Map())
const tableBodyRef = ref(null)
const selectedKeyMap = ref({})
const internalExpandedKeys = ref([])

function registerColumn(column) {
  if (!column?.uid) {
    return
  }
  columnsMap.set(column.uid, { ...column })
}

function unregisterColumn(uid) {
  columnsMap.delete(uid)
}

provide(tableContextKey, {
  registerColumn,
  unregisterColumn,
})

const rootAttrs = computed(() => ({
  class: attrs.class,
  style: attrs.style,
}))

const rows = computed(() => (Array.isArray(props.data) ? props.data : []))
const columns = computed(() => Array.from(columnsMap.values()))
const normalizedColumns = computed(() =>
  columns.value.map((column) => ({
    ...column,
    type: normalizeTableColumnType(column.type),
    fixed: normalizeFixedPosition(column.fixed),
  })),
)
const selectionColumn = computed(() =>
  normalizedColumns.value.find((column) => column.type === 'selection') || null,
)
const reserveSelection = computed(() => Boolean(selectionColumn.value?.reserveSelection))
const stickyOffsets = computed(() => buildStickyOffsets(normalizedColumns.value))
const normalizedExpandedKeys = computed(() =>
  normalizeExpandedKeys(props.expandRowKeys !== undefined ? props.expandRowKeys : internalExpandedKeys.value),
)
const tableClasses = computed(() => [
  'ui-table',
  'el-table',
  props.border ? 'el-table--border' : '',
  props.stripe ? 'el-table--striped' : '',
  props.size === 'small' ? 'el-table--small' : '',
])
const bodyWrapperStyle = computed(() => {
  if (props.maxHeight === undefined || props.maxHeight === null || props.maxHeight === '') {
    return {}
  }
  const maxHeight = typeof props.maxHeight === 'number' ? `${props.maxHeight}px` : String(props.maxHeight)
  return {
    maxHeight,
    overflow: 'auto',
  }
})

const currentPageSelectedRows = computed(() =>
  rows.value.filter((row, index) => selectedKeyMap.value[resolveTableRowKey(row, props.rowKey, index)]),
)
const allRowsSelected = computed(() =>
  rows.value.length > 0 && currentPageSelectedRows.value.length === rows.value.length,
)
const hasSelection = computed(() => currentPageSelectedRows.value.length > 0)
const tableWidth = computed(() =>
  normalizedColumns.value.reduce((sum, column) => {
    const fallback = column.type === 'selection' ? 55 : column.type === 'index' ? 64 : 160
    return sum + parseTableSize(column.width ?? column.minWidth, fallback)
  }, 0),
)

function buildScope(row, rowIndex, column) {
  return {
    row,
    $index: rowIndex,
    column,
  }
}

function getRowKey(row, index) {
  return resolveTableRowKey(row, props.rowKey, index)
}

function isRowExpanded(row, index) {
  return normalizedExpandedKeys.value.includes(getRowKey(row, index))
}

function emitSelectionChange() {
  emit('selection-change', currentPageSelectedRows.value)
}

function setRowSelected(row, rowIndex, selected) {
  const rowKey = getRowKey(row, rowIndex)
  if (!rowKey) {
    return
  }

  const nextMap = { ...selectedKeyMap.value }
  if (selected) {
    nextMap[rowKey] = true
  } else {
    delete nextMap[rowKey]
  }
  selectedKeyMap.value = nextMap
}

function handleToggleAllSelection(event) {
  const nextChecked = Boolean(event?.target?.checked)
  const nextMap = reserveSelection.value ? { ...selectedKeyMap.value } : {}

  rows.value.forEach((row, rowIndex) => {
    const rowKey = getRowKey(row, rowIndex)
    if (!rowKey) {
      return
    }
    if (nextChecked) {
      nextMap[rowKey] = true
    } else {
      delete nextMap[rowKey]
    }
  })

  selectedKeyMap.value = nextMap
  emitSelectionChange()
}

function handleToggleRowSelection(row, rowIndex, event) {
  setRowSelected(row, rowIndex, Boolean(event?.target?.checked))
  emitSelectionChange()
}

function toggleExpanded(row, rowIndex, expanded) {
  const rowKey = getRowKey(row, rowIndex)
  if (!rowKey) {
    return
  }

  const currentKeys = normalizeExpandedKeys(internalExpandedKeys.value)
  const alreadyExpanded = normalizedExpandedKeys.value.includes(rowKey)
  const nextExpanded = expanded === undefined ? !alreadyExpanded : Boolean(expanded)

  internalExpandedKeys.value = nextExpanded
    ? Array.from(new Set([...currentKeys, rowKey]))
    : currentKeys.filter((key) => key !== rowKey)

  emit('expand-change', row, nextExpanded)
}

function toggleRowExpansion(row, expanded) {
  const rowIndex = rows.value.findIndex((item, index) => getRowKey(item, index) === getRowKey(row, rows.value.indexOf(row)))
  if (rowIndex < 0) {
    return
  }
  toggleExpanded(rows.value[rowIndex], rowIndex, expanded)
}

function clearSelection() {
  selectedKeyMap.value = {}
  emitSelectionChange()
}

function toggleRowSelection(row, selected = undefined) {
  const rowIndex = rows.value.findIndex((item, index) => getRowKey(item, index) === getRowKey(row, rows.value.indexOf(row)))
  if (rowIndex < 0) {
    return
  }
  const rowKey = getRowKey(rows.value[rowIndex], rowIndex)
  const isSelected = Boolean(selectedKeyMap.value[rowKey])
  setRowSelected(rows.value[rowIndex], rowIndex, selected === undefined ? !isSelected : Boolean(selected))
  emitSelectionChange()
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  toggleRowExpansion,
  getSelectionRows: () => currentPageSelectedRows.value,
})

watch(
  rows,
  (nextRows) => {
    const currentPageKeys = new Set(
      nextRows.map((row, index) => getRowKey(row, index)).filter((key) => Boolean(key)),
    )

    if (!reserveSelection.value) {
      const nextMap = {}
      currentPageKeys.forEach((key) => {
        if (selectedKeyMap.value[key]) {
          nextMap[key] = true
        }
      })
      selectedKeyMap.value = nextMap
      return
    }

    const nextMap = { ...selectedKeyMap.value }
    Object.keys(nextMap).forEach((key) => {
      if (!nextMap[key]) {
        delete nextMap[key]
      }
    })
    selectedKeyMap.value = nextMap
  },
  { immediate: true },
)

onMounted(() => {
  nextTick(() => {
    tableBodyRef.value?.scrollTo?.({ top: 0 })
  })
})

onBeforeUnmount(() => {
  selectedKeyMap.value = {}
})

function resolveColumnStyle(column) {
  const fallback = column.type === 'selection' ? 55 : column.type === 'index' ? 64 : 160
  const width = column.width !== undefined ? parseTableSize(column.width, fallback) : undefined
  const minWidth = parseTableSize(column.minWidth, fallback)

  return {
    width: width ? `${width}px` : undefined,
    minWidth: `${minWidth}px`,
  }
}

function resolveStickyStyle(column) {
  if (column.fixed === 'left') {
    return {
      left: `${stickyOffsets.value.leftOffsets[column.uid] || 0}px`,
    }
  }

  if (column.fixed === 'right') {
    return {
      right: `${stickyOffsets.value.rightOffsets[column.uid] || 0}px`,
    }
  }

  return {}
}

function resolveCellValue(row, column) {
  if (!column.prop) {
    return ''
  }
  const value = row?.[column.prop]
  return value === undefined || value === null ? '' : String(value)
}
</script>

<template>
  <div v-bind="rootAttrs" :class="tableClasses">
    <div v-if="!rows.length" class="el-table__empty-block">
      <slot name="empty">
        <div class="el-table__empty-text">{{ emptyText }}</div>
      </slot>
    </div>

    <div v-else ref="tableBodyRef" class="el-table__inner-wrapper" :style="bodyWrapperStyle">
      <table class="el-table__body-table" :style="{ minWidth: `${tableWidth}px` }">
        <thead>
          <tr>
            <th
              v-for="column in normalizedColumns"
              :key="`header-${column.uid}`"
              class="el-table__cell"
              :class="[
                column.fixed ? `is-fixed-${column.fixed}` : '',
                column.type === 'selection' ? 'is-selection-column' : '',
              ]"
              :style="{ ...resolveColumnStyle(column), ...resolveStickyStyle(column) }"
            >
              <label v-if="column.type === 'selection'" class="ui-table__checkbox">
                <input
                  type="checkbox"
                  :checked="allRowsSelected"
                  :indeterminate="!allRowsSelected && hasSelection ? 'true' : undefined"
                  @change="handleToggleAllSelection"
                >
              </label>
              <span v-else>{{ column.label }}</span>
            </th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(row, rowIndex) in rows" :key="getRowKey(row, rowIndex) || rowIndex">
            <tr :class="['el-table__row', stripe && rowIndex % 2 === 1 ? 'el-table__row--striped' : '']">
              <td
                v-for="column in normalizedColumns"
                :key="`${getRowKey(row, rowIndex)}-${column.uid}`"
                class="el-table__cell"
                :class="[
                  column.fixed ? `is-fixed-${column.fixed}` : '',
                  column.showOverflowTooltip ? 'has-tooltip' : '',
                ]"
                :style="{ ...resolveColumnStyle(column), ...resolveStickyStyle(column) }"
              >
                <label v-if="column.type === 'selection'" class="ui-table__checkbox">
                  <input
                    type="checkbox"
                    :checked="Boolean(selectedKeyMap[getRowKey(row, rowIndex)])"
                    @change="handleToggleRowSelection(row, rowIndex, $event)"
                  >
                </label>

                <button
                  v-else-if="column.type === 'expand'"
                  type="button"
                  class="ui-table__expand-trigger"
                  :aria-expanded="String(isRowExpanded(row, rowIndex))"
                  @click="toggleExpanded(row, rowIndex)"
                >
                  {{ isRowExpanded(row, rowIndex) ? '收起' : '展开' }}
                </button>

                <span v-else-if="column.type === 'index'">
                  {{ rowIndex + 1 }}
                </span>

                <SlotRenderer
                  v-else-if="column.render"
                  :render="column.render"
                  :scope="buildScope(row, rowIndex, column)"
                />

                <span
                  v-else
                  class="ui-table__cell-text"
                  :title="column.showOverflowTooltip ? resolveCellValue(row, column) : undefined"
                >
                  {{ resolveCellValue(row, column) }}
                </span>
              </td>
            </tr>

            <tr
              v-if="normalizedColumns.some((column) => column.type === 'expand') && isRowExpanded(row, rowIndex)"
              class="el-table__expanded-row"
            >
              <td class="el-table__cell el-table__expanded-cell" :colspan="normalizedColumns.length">
                <SlotRenderer
                  v-for="column in normalizedColumns.filter((item) => item.type === 'expand' && item.render)"
                  :key="`expand-${column.uid}-${getRowKey(row, rowIndex)}`"
                  :render="column.render"
                  :scope="buildScope(row, rowIndex, column)"
                />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.ui-table {
  position: relative;
  width: 100%;
  border-radius: 16px;
  background: var(--qb-surface-card);
  overflow: hidden;
}

.ui-table.el-table--border {
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 84%, white 16%);
}

.el-table__inner-wrapper {
  width: 100%;
  overflow: auto;
}

.el-table__body-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.el-table__cell {
  position: relative;
  padding: 12px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-muted) 74%, white 26%);
  background: inherit;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.5;
  text-align: left;
  vertical-align: middle;
  box-sizing: border-box;
}

thead .el-table__cell {
  position: sticky;
  top: 0;
  z-index: 3;
  background: color-mix(in srgb, var(--qb-surface-solid) 96%, white 4%);
  color: var(--qb-text-secondary-strong);
  font-weight: 700;
}

.el-table__row--striped .el-table__cell {
  background: color-mix(in srgb, var(--qb-bg-muted) 42%, white 58%);
}

.el-table__cell.is-fixed-left,
.el-table__cell.is-fixed-right {
  position: sticky;
  z-index: 2;
}

thead .el-table__cell.is-fixed-left,
thead .el-table__cell.is-fixed-right {
  z-index: 4;
}

.el-table__cell.is-fixed-left {
  box-shadow: 1px 0 0 color-mix(in srgb, var(--qb-border-muted) 70%, white 30%);
}

.el-table__cell.is-fixed-right {
  box-shadow: -1px 0 0 color-mix(in srgb, var(--qb-border-muted) 70%, white 30%);
}

.el-table__empty-block {
  display: grid;
  place-items: center;
  min-height: 168px;
  padding: 24px;
}

.el-table__empty-text {
  color: var(--qb-text-meta);
  font-size: 14px;
}

.ui-table__checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ui-table__checkbox input {
  width: 16px;
  height: 16px;
  accent-color: var(--qb-primary-student);
}

.ui-table__expand-trigger {
  border: 0;
  background: transparent;
  color: var(--qb-primary-student);
  cursor: pointer;
  padding: 0;
  font: inherit;
}

.ui-table__cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.el-table__expanded-row .el-table__expanded-cell {
  padding: 0;
  background: color-mix(in srgb, var(--qb-bg-muted) 34%, white 66%);
}

.ui-table.el-table--small .el-table__cell {
  padding: 9px 12px;
  font-size: 13px;
}
</style>
