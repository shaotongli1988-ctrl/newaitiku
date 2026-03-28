<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, reactive, ref, watch } from 'vue'
import {
  filterSelectOptions,
  findSelectOption,
  isSelectValueEmpty,
  isSelectValueEqual,
  normalizeSelectValue,
  selectContextKey,
  toggleSelectMultipleValue,
} from './selectShared'

const props = defineProps({
  modelValue: {
    type: [Array, String, Number, Boolean, Object],
    default: undefined,
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
  multiple: {
    type: Boolean,
    default: false,
  },
  collapseTags: {
    type: Boolean,
    default: false,
  },
  noDataText: {
    type: String,
    default: '暂无数据',
  },
  noMatchText: {
    type: String,
    default: '暂无匹配项',
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'clear', 'visible-change'])

const rootRef = ref(null)
const queryInputRef = ref(null)
const isOpen = ref(false)
const keyword = ref('')
const optionsMap = reactive(new Map())

function registerOption(option) {
  if (!option?.uid) {
    return
  }

  optionsMap.set(option.uid, option)
}

function unregisterOption(uid) {
  optionsMap.delete(uid)
}

provide(selectContextKey, {
  registerOption,
  unregisterOption,
})

const options = computed(() => Array.from(optionsMap.values()))
const normalizedValue = computed(() => normalizeSelectValue(props.modelValue, { multiple: props.multiple }))
const filteredOptions = computed(() => filterSelectOptions(options.value, props.filterable ? keyword.value : ''))

const selectedOptions = computed(() => {
  if (props.multiple) {
    return normalizedValue.value
      .map((value) => findSelectOption(options.value, value))
      .filter(Boolean)
  }

  const selectedOption = findSelectOption(options.value, normalizedValue.value)
  return selectedOption ? [selectedOption] : []
})

const hasSelection = computed(() => !isSelectValueEmpty(normalizedValue.value, { multiple: props.multiple }))
const showClear = computed(() => props.clearable && !props.disabled && hasSelection.value)

const selectClasses = computed(() => [
  'ui-select',
  'el-select',
  props.disabled ? 'is-disabled' : '',
  isOpen.value ? 'is-focus' : '',
  hasSelection.value ? 'has-value' : '',
  props.multiple ? 'el-select--multiple' : '',
])

const singleDisplayLabel = computed(() => selectedOptions.value[0]?.label || '')

const multipleDisplayOptions = computed(() => {
  if (!props.multiple) {
    return []
  }

  if (props.collapseTags && selectedOptions.value.length > 1) {
    return selectedOptions.value.slice(0, 1)
  }

  return selectedOptions.value
})

const hiddenTagCount = computed(() => {
  if (!props.multiple || !props.collapseTags || selectedOptions.value.length <= 1) {
    return 0
  }

  return selectedOptions.value.length - 1
})

function emitValue(nextValue) {
  if (isSelectValueEqual(nextValue, props.modelValue, { multiple: props.multiple })) {
    return
  }

  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

function closeDropdown() {
  if (!isOpen.value) {
    return
  }

  isOpen.value = false
  keyword.value = ''
  emit('visible-change', false)
}

async function openDropdown() {
  if (props.disabled || isOpen.value) {
    return
  }

  isOpen.value = true
  emit('visible-change', true)

  if (props.filterable) {
    await nextTick()
    queryInputRef.value?.focus()
  }
}

function toggleDropdown() {
  if (props.disabled) {
    return
  }

  if (isOpen.value) {
    closeDropdown()
    return
  }

  openDropdown()
}

function selectOption(option) {
  if (!option || option.disabled) {
    return
  }

  let nextValue
  if (props.multiple) {
    nextValue = toggleSelectMultipleValue(normalizedValue.value, option.value)
  } else {
    nextValue = option.value
  }

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

  const nextValue = props.multiple ? [] : undefined
  keyword.value = ''
  emitValue(nextValue)
  emit('clear')
  closeDropdown()
}

function isSelected(option) {
  if (props.multiple) {
    return normalizedValue.value.includes(option.value)
  }

  return normalizedValue.value === option.value
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
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    openDropdown()
  }
}

watch(
  () => props.modelValue,
  () => {
    if (!props.multiple && !hasSelection.value) {
      keyword.value = ''
    }
  },
)

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleDocumentPointerDown)
})
</script>

<template>
  <div ref="rootRef" :class="selectClasses">
    <div class="ui-select__registry" aria-hidden="true">
      <slot />
    </div>

    <div
      class="el-select__wrapper"
      :tabindex="disabled ? -1 : 0"
      role="combobox"
      :aria-expanded="String(isOpen)"
      :aria-disabled="String(disabled)"
      @click="toggleDropdown"
      @keydown="handleKeydown"
    >
      <div class="el-select__selection">
        <template v-if="multiple">
          <div v-if="multipleDisplayOptions.length" class="el-select__tags">
            <span
              v-for="option in multipleDisplayOptions"
              :key="String(option.value)"
              class="el-select__tag"
            >
              {{ option.label }}
            </span>
            <span v-if="hiddenTagCount" class="el-select__tag el-select__tag--summary">
              +{{ hiddenTagCount }}
            </span>
          </div>
          <span v-else class="el-select__placeholder">{{ placeholder }}</span>
        </template>

        <template v-else>
          <span v-if="singleDisplayLabel" class="el-select__value">{{ singleDisplayLabel }}</span>
          <span v-else class="el-select__placeholder">{{ placeholder }}</span>
        </template>
      </div>

      <div class="el-select__suffix">
        <button
          v-if="showClear"
          type="button"
          class="el-select__clear"
          aria-label="清除选择"
          @click="clearValue"
        >
          ×
        </button>
        <span class="el-select__caret" :class="{ 'is-open': isOpen }" aria-hidden="true">▾</span>
      </div>
    </div>

    <div v-if="isOpen" class="el-select-dropdown">
      <div v-if="filterable" class="el-select-dropdown__search">
        <input
          ref="queryInputRef"
          v-model="keyword"
          type="text"
          class="el-select-dropdown__input"
          placeholder="输入关键字筛选"
          @click.stop
        >
      </div>

      <ul class="el-scrollbar__view el-select-dropdown__list" :aria-multiselectable="multiple ? 'true' : undefined">
        <li
          v-for="option in filteredOptions"
          :key="String(option.uid)"
          class="el-select-dropdown__item"
          :class="{ 'is-selected': isSelected(option), 'is-disabled': option.disabled }"
          @click.stop="selectOption(option)"
        >
          <span>{{ option.label }}</span>
          <span v-if="isSelected(option)" class="el-select-dropdown__check" aria-hidden="true">✓</span>
        </li>
        <li v-if="!filteredOptions.length" class="el-select-dropdown__empty">
          {{ options.length ? noMatchText : noDataText }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.ui-select {
  position: relative;
  display: inline-flex;
  width: 100%;
  min-width: 0;
}

.ui-select.is-disabled {
  opacity: 0.68;
}

.ui-select__registry {
  display: none;
}

.el-select__wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-height: 40px;
  padding: 7px 12px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 12px;
  background: var(--qb-surface-strong);
  box-sizing: border-box;
  cursor: pointer;
  transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.ui-select.is-focus .el-select__wrapper,
.ui-select:not(.is-disabled) .el-select__wrapper:focus,
.ui-select:not(.is-disabled) .el-select__wrapper:focus-visible {
  border-color: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-student) 16%, white 84%);
  outline: none;
}

.ui-select:not(.is-disabled) .el-select__wrapper:hover {
  border-color: color-mix(in srgb, var(--qb-primary-student) 38%, white 62%);
}

.ui-select.is-disabled .el-select__wrapper {
  cursor: not-allowed;
  background: color-mix(in srgb, var(--qb-surface-muted) 88%, white 12%);
}

.el-select__selection {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  align-items: center;
}

.el-select__value,
.el-select__placeholder {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 1.5;
}

.el-select__value {
  color: var(--qb-text-primary);
}

.el-select__placeholder {
  color: var(--qb-text-muted);
}

.el-select__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.el-select__tag {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 12%, white 88%);
  color: var(--qb-primary-student);
  font-size: 12px;
  line-height: 1.5;
  white-space: nowrap;
}

.el-select__tag--summary {
  background: color-mix(in srgb, var(--qb-text-muted) 14%, white 86%);
  color: var(--qb-text-secondary);
}

.el-select__suffix {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  color: var(--qb-text-muted);
}

.el-select__clear {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.el-select__caret {
  display: inline-flex;
  transition: transform 180ms ease;
}

.el-select__caret.is-open {
  transform: rotate(180deg);
}

.el-select-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  width: 100%;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 92%, white 8%);
  border-radius: 14px;
  background: var(--qb-surface-strong);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

.el-select-dropdown__search {
  padding: 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-muted) 84%, white 16%);
}

.el-select-dropdown__input {
  width: 100%;
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 10px;
  background: var(--qb-surface-strong);
  color: var(--qb-text-primary);
  box-sizing: border-box;
}

.el-select-dropdown__input:focus,
.el-select-dropdown__input:focus-visible {
  border-color: var(--qb-primary-student);
  outline: none;
}

.el-select-dropdown__list {
  max-height: 280px;
  margin: 0;
  padding: 8px;
  overflow: auto;
  list-style: none;
}

.el-select-dropdown__item,
.el-select-dropdown__empty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 38px;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.45;
}

.el-select-dropdown__item {
  color: var(--qb-text-primary);
  cursor: pointer;
}

.el-select-dropdown__item.is-selected {
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
}

.el-select-dropdown__item.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.el-select-dropdown__item:not(.is-disabled):hover {
  background: color-mix(in srgb, var(--qb-primary-student) 8%, white 92%);
}

.el-select-dropdown__empty {
  justify-content: center;
  color: var(--qb-text-muted);
}

.el-select-dropdown__check {
  font-size: 13px;
}
</style>
