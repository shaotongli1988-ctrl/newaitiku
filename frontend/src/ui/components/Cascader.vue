<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  buildCascaderColumns,
  buildCascaderSelections,
  filterCascaderSelections,
  findCascaderSelection,
  formatCascaderSelectionLabel,
  resolveCascaderConfig,
  toCascaderModelValue,
} from './cascaderShared'

const props = defineProps({
  modelValue: {
    type: [Array, String, Number, Boolean],
    default: undefined,
  },
  options: {
    type: Array,
    default: () => [],
  },
  props: {
    type: Object,
    default: () => ({}),
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  filterable: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  teleported: {
    type: Boolean,
    default: true,
  },
  showAllLevels: {
    type: Boolean,
    default: true,
  },
  separator: {
    type: String,
    default: ' / ',
  },
  collapseTags: {
    type: Boolean,
    default: false,
  },
  collapseTagsTooltip: {
    type: Boolean,
    default: false,
  },
  expandTrigger: {
    type: String,
    default: 'click',
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'clear', 'visible-change'])

const rootRef = ref(null)
const queryInputRef = ref(null)
const isOpen = ref(false)
const keyword = ref('')
const activePath = ref([])

const config = computed(() => resolveCascaderConfig(props.props))
const selections = computed(() => buildCascaderSelections(props.options, props.props))
const selection = computed(() => findCascaderSelection(props.options, props.modelValue, props.props))
const filteredSelections = computed(() => filterCascaderSelections(selections.value, keyword.value))
const displayLabel = computed(() => formatCascaderSelectionLabel(selection.value, {
  showAllLevels: props.showAllLevels,
  separator: props.separator,
}))
const hasSelection = computed(() => {
  if (config.value.emitPath) {
    return Array.isArray(props.modelValue) && props.modelValue.length > 0
  }
  return props.modelValue !== '' && props.modelValue !== null && props.modelValue !== undefined
})

const cascaderClasses = computed(() => [
  'ui-cascader',
  'el-cascader',
  props.disabled ? 'is-disabled' : '',
  isOpen.value ? 'is-focus' : '',
  hasSelection.value ? 'has-value' : '',
])

const columns = computed(() => buildCascaderColumns(
  props.options,
  activePath.value.length ? activePath.value : (selection.value?.path || []),
  props.props,
))

function updateVisible(visible) {
  if (isOpen.value === visible) {
    return
  }

  isOpen.value = visible
  emit('visible-change', visible)
  if (!visible) {
    keyword.value = ''
  }
}

async function openDropdown() {
  if (props.disabled) {
    return
  }

  activePath.value = selection.value?.path ? [...selection.value.path] : []
  updateVisible(true)

  if (props.filterable) {
    await nextTick()
    queryInputRef.value?.focus()
  }
}

function closeDropdown() {
  updateVisible(false)
}

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown()
    return
  }
  openDropdown()
}

function emitSelection(nextSelection) {
  const nextValue = toCascaderModelValue(nextSelection, props.props)
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

function clearValue(event) {
  event?.stopPropagation?.()
  if (!props.clearable || props.disabled || !hasSelection.value) {
    return
  }
  const emptyValue = config.value.emitPath ? [] : undefined
  emit('update:modelValue', emptyValue)
  emit('change', emptyValue)
  emit('clear')
  closeDropdown()
}

function getNodeValue(node) {
  return node?.[config.value.valueKey]
}

function getNodeLabel(node) {
  const rawLabel = node?.[config.value.labelKey]
  return String(rawLabel ?? getNodeValue(node) ?? '')
}

function getNodeChildren(node) {
  const childNodes = node?.[config.value.childrenKey]
  return Array.isArray(childNodes) ? childNodes : []
}

function isNodeSelected(node, parentPath = []) {
  const nextPath = [...parentPath, getNodeValue(node)]
  const currentPath = selection.value?.path || []
  return nextPath.length === currentPath.length
    && nextPath.every((item, index) => item === currentPath[index])
}

function isNodeActive(node, parentPath = []) {
  const nextPath = [...parentPath, getNodeValue(node)]
  return nextPath.every((item, index) => item === activePath.value[index])
}

function canNodeSelect(node) {
  const hasChildren = getNodeChildren(node).length > 0
  return config.value.checkStrictly || !hasChildren
}

function handleNodeExpand(node, parentPath = []) {
  if (node?.disabled) {
    return
  }
  activePath.value = [...parentPath, getNodeValue(node)]
}

function handleNodeSelect(node, parentPath = []) {
  if (node?.disabled) {
    return
  }

  const path = [...parentPath, getNodeValue(node)]
  const selected = selections.value.find((item) => (
    item.path.length === path.length
    && item.path.every((segment, index) => segment === path[index])
  ))

  if (!selected) {
    handleNodeExpand(node, parentPath)
    return
  }

  activePath.value = [...path]
  emitSelection(selected)
  closeDropdown()
}

function handleDocumentPointerDown(event) {
  if (!rootRef.value?.contains(event.target)) {
    closeDropdown()
  }
}

function handleKeydown(event) {
  if (props.disabled) {
    return
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleDropdown()
    return
  }

  if (event.key === 'Escape') {
    closeDropdown()
  }
}

watch(
  () => props.modelValue,
  () => {
    activePath.value = selection.value?.path ? [...selection.value.path] : []
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleDocumentPointerDown)
})
</script>

<template>
  <div ref="rootRef" :class="cascaderClasses">
    <div
      class="el-input el-input--suffix"
      :tabindex="disabled ? -1 : 0"
      role="combobox"
      :aria-expanded="String(isOpen)"
      :aria-disabled="String(disabled)"
      @click="toggleDropdown"
      @keydown="handleKeydown"
    >
      <div class="el-input__wrapper">
        <span v-if="displayLabel" class="el-input__inner ui-cascader__value">{{ displayLabel }}</span>
        <span v-else class="el-input__inner ui-cascader__placeholder">{{ placeholder }}</span>
        <span v-if="loading" class="ui-cascader__loading">加载中</span>
        <button
          v-else-if="clearable && hasSelection && !disabled"
          type="button"
          class="ui-cascader__clear"
          aria-label="清除选择"
          @click="clearValue"
        >
          ×
        </button>
        <span v-else class="ui-cascader__caret" :class="{ 'is-open': isOpen }">▾</span>
      </div>
    </div>

    <div v-if="isOpen" class="el-cascader__dropdown">
      <div v-if="filterable" class="ui-cascader__search">
        <input
          ref="queryInputRef"
          v-model="keyword"
          class="ui-cascader__search-input"
          type="text"
          placeholder="输入关键字筛选"
          @click.stop
        >
      </div>

      <div v-if="loading" class="ui-cascader__empty">加载中...</div>
      <div v-else-if="filterable && keyword.trim()" class="ui-cascader__filter-panel">
        <button
          v-for="item in filteredSelections"
          :key="item.path.join('__')"
          type="button"
          class="ui-cascader__filter-item"
          :class="{ 'is-selected': formatCascaderSelectionLabel(item) === formatCascaderSelectionLabel(selection) }"
          @click="handleNodeSelect(item.node, item.path.slice(0, -1))"
        >
          {{ formatCascaderSelectionLabel(item, { separator }) }}
        </button>
        <div v-if="!filteredSelections.length" class="ui-cascader__empty">暂无匹配项</div>
      </div>
      <div v-else class="ui-cascader__panels">
        <div
          v-for="(column, columnIndex) in columns"
          :key="`column-${columnIndex}`"
          class="el-cascader-menu"
        >
          <button
            v-for="node in column"
            :key="String(getNodeValue(node))"
            type="button"
            class="el-cascader-node"
            :class="{
              'in-active-path': isNodeActive(node, activePath.slice(0, columnIndex)),
              'is-selected': isNodeSelected(node, activePath.slice(0, columnIndex)),
              'is-disabled': node?.disabled,
            }"
            @click="handleNodeSelect(node, activePath.slice(0, columnIndex))"
          >
            <span class="el-cascader-node__label">{{ getNodeLabel(node) }}</span>
            <span
              v-if="getNodeChildren(node).length"
              class="el-cascader-node__postfix"
              @click.stop="handleNodeExpand(node, activePath.slice(0, columnIndex))"
            >
              ›
            </span>
          </button>
        </div>
        <div v-if="!columns.length" class="ui-cascader__empty">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ui-cascader {
  position: relative;
  display: inline-flex;
  width: 100%;
}

.ui-cascader.is-disabled {
  opacity: 0.68;
}

.el-input {
  width: 100%;
  cursor: pointer;
}

.el-input__wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 40px;
  padding: 7px 12px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 12px;
  background: var(--qb-surface-strong);
  box-sizing: border-box;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.ui-cascader.is-focus .el-input__wrapper,
.el-input:focus .el-input__wrapper,
.el-input:focus-visible .el-input__wrapper {
  border-color: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-student) 16%, white 84%);
  outline: none;
}

.ui-cascader__value,
.ui-cascader__placeholder {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 1.5;
}

.ui-cascader__value {
  color: var(--qb-text-primary);
}

.ui-cascader__placeholder {
  color: var(--qb-text-muted);
}

.ui-cascader__loading,
.ui-cascader__caret,
.ui-cascader__clear {
  flex: 0 0 auto;
  color: var(--qb-text-muted);
}

.ui-cascader__clear {
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.ui-cascader__caret {
  transition: transform 180ms ease;
}

.ui-cascader__caret.is-open {
  transform: rotate(180deg);
}

.el-cascader__dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  width: 100%;
  min-width: 280px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 92%, white 8%);
  border-radius: 14px;
  background: var(--qb-surface-strong);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

.ui-cascader__search {
  padding: 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-muted) 84%, white 16%);
}

.ui-cascader__search-input {
  width: 100%;
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 10px;
  box-sizing: border-box;
}

.ui-cascader__search-input:focus,
.ui-cascader__search-input:focus-visible {
  border-color: var(--qb-primary-student);
  outline: none;
}

.ui-cascader__panels {
  display: flex;
  min-height: 220px;
}

.el-cascader-menu {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  min-width: 0;
  max-height: 280px;
  padding: 8px;
  overflow: auto;
  border-right: 1px solid color-mix(in srgb, var(--qb-border-muted) 84%, white 16%);
}

.el-cascader-menu:last-child {
  border-right: 0;
}

.el-cascader-node,
.ui-cascader__filter-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 38px;
  padding: 8px 10px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.45;
  text-align: left;
  cursor: pointer;
}

.el-cascader-node:hover,
.ui-cascader__filter-item:hover,
.el-cascader-node.in-active-path,
.ui-cascader__filter-item.is-selected,
.el-cascader-node.is-selected {
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
}

.el-cascader-node.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.el-cascader-node__label {
  min-width: 0;
  flex: 1 1 auto;
}

.el-cascader-node__postfix {
  flex: 0 0 auto;
  color: inherit;
}

.ui-cascader__filter-panel {
  display: flex;
  flex-direction: column;
  max-height: 280px;
  padding: 8px;
  overflow: auto;
}

.ui-cascader__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  padding: 16px;
  color: var(--qb-text-muted);
  font-size: 14px;
}
</style>
