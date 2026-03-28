<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import {
  buildTreeLabelMap,
  flattenTreeNodes,
  normalizeTreeSelectValue,
  toggleTreeValue,
} from './treeShared'

const props = defineProps({
  checkStrictly: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  collapseTags: {
    type: Boolean,
    default: false,
  },
  collapseTagsTooltip: {
    type: Boolean,
    default: false,
  },
  data: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  modelValue: {
    type: [Array, String, Number],
    default: undefined,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: '',
  },
  renderAfterExpand: {
    type: Boolean,
    default: true,
  },
  showCheckbox: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'clear', 'visible-change'])

const rootRef = ref(null)
const isOpen = ref(false)

const flatRows = computed(() => flattenTreeNodes(props.data))
const labelMap = computed(() => buildTreeLabelMap(props.data))
const normalizedValue = computed(() => normalizeTreeSelectValue(props.modelValue, {
  multiple: props.multiple,
}))
const selectedKeys = computed(() => (
  props.multiple
    ? normalizedValue.value
    : (normalizedValue.value ? [normalizedValue.value] : [])
))
const selectedLabels = computed(() => selectedKeys.value.map((key) => labelMap.value.get(key)).filter(Boolean))
const hiddenTagCount = computed(() => (
  props.multiple && props.collapseTags && selectedLabels.value.length > 1
    ? selectedLabels.value.length - 1
    : 0
))
const visibleLabels = computed(() => (
  hiddenTagCount.value > 0
    ? selectedLabels.value.slice(0, 1)
    : selectedLabels.value
))
const showClear = computed(() => props.clearable && !props.disabled && selectedKeys.value.length > 0)
const treeSelectClasses = computed(() => [
  'ui-tree-select',
  'el-select',
  props.disabled ? 'is-disabled' : '',
  isOpen.value ? 'is-focus' : '',
])

function updateVisible(nextVisible) {
  if (isOpen.value === nextVisible) {
    return
  }
  isOpen.value = nextVisible
  emit('visible-change', nextVisible)
}

function openDropdown() {
  if (props.disabled) {
    return
  }
  updateVisible(true)
}

function closeDropdown() {
  updateVisible(false)
}

function toggleDropdown() {
  if (props.disabled) {
    return
  }
  updateVisible(!isOpen.value)
}

function emitValue(nextValue) {
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

function toggleRow(row) {
  if (props.disabled) {
    return
  }

  const nextValue = toggleTreeValue(
    props.multiple ? selectedKeys.value : normalizedValue.value,
    row.key,
    { multiple: props.multiple },
  )
  emitValue(nextValue)
  if (!props.multiple) {
    closeDropdown()
  }
}

function clearValue(event) {
  event?.stopPropagation?.()
  if (!showClear.value) {
    return
  }
  const nextValue = props.multiple ? [] : ''
  emitValue(nextValue)
  emit('clear')
}

function isChecked(row) {
  return selectedKeys.value.includes(row.key)
}

function handleDocumentPointerDown(event) {
  if (!rootRef.value?.contains(event.target)) {
    closeDropdown()
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
}

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('pointerdown', handleDocumentPointerDown)
  }
})

watch(
  () => props.modelValue,
  async () => {
    await nextTick()
  },
)
</script>

<template>
  <div
    ref="rootRef"
    :class="treeSelectClasses"
  >
    <div
      class="el-select__wrapper"
      role="button"
      tabindex="0"
      @click="toggleDropdown"
      @keydown.enter.prevent="toggleDropdown"
      @keydown.space.prevent="toggleDropdown"
    >
      <div v-if="visibleLabels.length" class="el-select__selection">
        <span
          v-for="label in visibleLabels"
          :key="label"
          class="el-tag el-tag--info"
          :title="collapseTagsTooltip ? selectedLabels.join('、') : undefined"
        >
          {{ label }}
        </span>
        <span v-if="hiddenTagCount > 0" class="ui-tree-select__more">+{{ hiddenTagCount }}</span>
      </div>
      <span v-else class="ui-tree-select__placeholder">
        {{ placeholder || '请选择' }}
      </span>

      <div class="ui-tree-select__actions">
        <button
          v-if="showClear"
          type="button"
          class="ui-tree-select__clear"
          aria-label="清空选择"
          @click.stop="clearValue"
        >
          x
        </button>
        <span class="ui-tree-select__caret">▾</span>
      </div>
    </div>

    <div v-if="isOpen" class="ui-tree-select__panel">
      <div class="ui-tree-select__panel-body">
        <label
          v-for="row in flatRows"
          :key="row.key"
          class="ui-tree-select__row"
          :style="{ '--ui-tree-level': row.level }"
        >
          <input
            v-if="showCheckbox || multiple"
            type="checkbox"
            :checked="isChecked(row)"
            :disabled="disabled"
            @change="toggleRow(row)"
          >
          <button
            v-else
            type="button"
            class="ui-tree-select__option"
            @click="toggleRow(row)"
          >
            {{ row.label }}
          </button>
          <span v-if="showCheckbox || multiple" class="ui-tree-select__label" @click.prevent="toggleRow(row)">
            {{ row.label }}
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ui-tree-select {
  position: relative;
  width: 100%;
}

.ui-tree-select.is-disabled {
  opacity: 0.68;
}

.el-select__wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 40px;
  padding: 7px 12px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 12px;
  background: var(--qb-surface-strong);
  box-sizing: border-box;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.ui-tree-select:not(.is-disabled).is-focus .el-select__wrapper {
  border-color: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-student) 16%, white 84%);
}

.el-select__selection {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex-wrap: wrap;
}

.el-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
  font-size: 12px;
}

.ui-tree-select__placeholder {
  color: var(--qb-text-muted);
  font-size: 14px;
}

.ui-tree-select__actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.ui-tree-select__clear {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--qb-text-muted);
  font-size: 16px;
  cursor: pointer;
}

.ui-tree-select__caret {
  color: var(--qb-text-muted);
  font-size: 12px;
}

.ui-tree-select__more {
  color: var(--qb-text-secondary);
  font-size: 12px;
}

.ui-tree-select__panel {
  position: absolute;
  z-index: 60;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  border: 1px solid var(--qb-border-muted);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 48px -32px rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(10px);
}

.ui-tree-select__panel-body {
  display: grid;
  gap: 4px;
  max-height: 280px;
  overflow: auto;
  padding: 8px;
}

.ui-tree-select__row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 8px calc(10px + var(--ui-tree-level, 0) * 18px);
  border-radius: 12px;
  cursor: pointer;
}

.ui-tree-select__row:hover {
  background: color-mix(in srgb, var(--qb-primary-student) 8%, white 92%);
}

.ui-tree-select__label,
.ui-tree-select__option {
  color: var(--qb-text-primary);
  font-size: 14px;
}

.ui-tree-select__option {
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}
</style>
