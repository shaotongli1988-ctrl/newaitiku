<script setup>
import { computed, onBeforeUnmount, ref, useAttrs } from 'vue'
import {
  resolveAutocompleteItemLabel,
  runAutocompleteFetcher,
} from './autocompleteShared'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  clearable: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  fetchSuggestions: {
    type: Function,
    default: undefined,
  },
  modelValue: {
    type: [String, Number],
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  valueKey: {
    type: String,
    default: 'value',
  },
})

const emit = defineEmits([
  'update:modelValue',
  'input',
  'change',
  'focus',
  'blur',
  'select',
  'clear',
])

const attrs = useAttrs()
const rootRef = ref(null)
const inputRef = ref(null)
const isOpen = ref(false)
const suggestions = ref([])
const activeFetchToken = ref(0)

const rootAttrs = computed(() => ({
  class: attrs.class,
  style: attrs.style,
}))

const controlAttrs = computed(() => {
  const nextAttrs = {}
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === 'class' || key === 'style') {
      return
    }
    nextAttrs[key] = value
  })
  return nextAttrs
})

const normalizedValue = computed(() => String(props.modelValue ?? ''))
const showClear = computed(() => props.clearable && !props.disabled && Boolean(normalizedValue.value))
const autocompleteClasses = computed(() => [
  'ui-autocomplete',
  'el-autocomplete',
  props.disabled ? 'is-disabled' : '',
  isOpen.value ? 'is-focus' : '',
])

async function loadSuggestions(queryString) {
  const fetchToken = activeFetchToken.value + 1
  activeFetchToken.value = fetchToken
  const nextItems = await runAutocompleteFetcher(props.fetchSuggestions, queryString)
  if (fetchToken !== activeFetchToken.value) {
    return
  }
  suggestions.value = nextItems
  isOpen.value = nextItems.length > 0
}

function updateValue(nextValue) {
  emit('update:modelValue', nextValue)
  emit('input', nextValue)
}

function handleInput(event) {
  const nextValue = String(event?.target?.value ?? '')
  updateValue(nextValue)
  loadSuggestions(nextValue)
}

function handleFocus(event) {
  emit('focus', event)
  loadSuggestions(normalizedValue.value)
}

function handleBlur(event) {
  window.setTimeout(() => {
    isOpen.value = false
  }, 120)
  emit('blur', event)
}

function handleClear() {
  if (!showClear.value) {
    return
  }
  suggestions.value = []
  isOpen.value = false
  updateValue('')
  emit('change', '')
  emit('clear')
  inputRef.value?.focus()
}

function selectItem(item) {
  const nextValue = resolveAutocompleteItemLabel(item, props.valueKey)
  updateValue(nextValue)
  emit('change', nextValue)
  emit('select', item)
  suggestions.value = []
  isOpen.value = false
}

function handleDocumentPointerDown(event) {
  if (!rootRef.value?.contains(event.target)) {
    isOpen.value = false
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
</script>

<template>
  <div
    ref="rootRef"
    v-bind="rootAttrs"
    :class="autocompleteClasses"
  >
    <div class="el-input el-input--suffix">
      <div class="el-input__wrapper">
        <input
          ref="inputRef"
          v-bind="controlAttrs"
          class="el-input__inner"
          :value="normalizedValue"
          :placeholder="placeholder || undefined"
          :disabled="disabled"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
        >

        <span v-if="showClear" class="el-input__suffix">
          <button
            type="button"
            class="ui-autocomplete__clear"
            aria-label="清空搜索"
            @mousedown.prevent
            @click.stop="handleClear"
          >
            x
          </button>
        </span>
      </div>
    </div>

    <div v-if="isOpen" class="el-autocomplete-suggestion">
      <ul class="el-scrollbar__view el-autocomplete-suggestion__list">
        <li
          v-for="(item, index) in suggestions"
          :key="item.id || item.value || item.label || index"
          class="el-autocomplete-suggestion__list-item"
          @mousedown.prevent="selectItem(item)"
        >
          <slot name="default" :item="item">
            {{ resolveAutocompleteItemLabel(item, valueKey) }}
          </slot>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.ui-autocomplete {
  position: relative;
  width: 100%;
}

.ui-autocomplete.is-disabled {
  opacity: 0.68;
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

.ui-autocomplete:not(.is-disabled).is-focus .el-input__wrapper,
.ui-autocomplete:not(.is-disabled):focus-within .el-input__wrapper {
  border-color: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-student) 16%, white 84%);
}

.el-input__inner {
  width: 100%;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.5;
  outline: none;
}

.el-input__suffix {
  flex: 0 0 auto;
}

.ui-autocomplete__clear {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--qb-text-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.el-autocomplete-suggestion {
  position: absolute;
  z-index: 40;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  max-height: 280px;
  overflow: auto;
  padding: 8px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 48px -32px rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(10px);
}

.el-autocomplete-suggestion__list {
  display: grid;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.el-autocomplete-suggestion__list-item {
  padding: 10px 12px;
  border-radius: 12px;
  color: var(--qb-text-primary);
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease;
}

.el-autocomplete-suggestion__list-item:hover {
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
}
</style>
