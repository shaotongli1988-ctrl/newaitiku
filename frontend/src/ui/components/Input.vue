<script setup>
import { computed, ref, useAttrs } from 'vue'
import {
  normalizeInputValue,
  resolveInputControlType,
  resolveInputMaxlength,
  shouldShowInputClear,
} from './inputShared'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  maxlength: {
    type: [String, Number],
    default: undefined,
  },
  rows: {
    type: [String, Number],
    default: 2,
  },
  showPassword: {
    type: Boolean,
    default: false,
  },
  showWordLimit: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'update:modelValue',
  'input',
  'change',
  'blur',
  'focus',
  'clear',
])

const attrs = useAttrs()
const controlRef = ref(null)
const passwordVisible = ref(false)

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

const normalizedValue = computed(() => normalizeInputValue(props.modelValue))
const isTextarea = computed(() => props.type === 'textarea')
const maxLength = computed(() => resolveInputMaxlength(props.maxlength))
const showWordLimitIndicator = computed(() => props.showWordLimit && maxLength.value !== undefined)
const wordCount = computed(() => normalizedValue.value.length)
const hasValue = computed(() => normalizedValue.value.length > 0)
const showClear = computed(() =>
  shouldShowInputClear({
    clearable: props.clearable,
    disabled: props.disabled,
    readonly: props.readonly,
    hasValue: hasValue.value,
  }),
)
const allowPasswordToggle = computed(() =>
  props.type === 'password' && props.showPassword && !isTextarea.value,
)
const resolvedType = computed(() =>
  resolveInputControlType(props.type, allowPasswordToggle.value, passwordVisible.value),
)

const inputClasses = computed(() => [
  'ui-input',
  'el-input',
  props.disabled ? 'is-disabled' : '',
  props.readonly ? 'is-readonly' : '',
  showClear.value || allowPasswordToggle.value ? 'el-input--suffix' : '',
])

const textareaClasses = computed(() => [
  'ui-textarea',
  'el-textarea',
  props.disabled ? 'is-disabled' : '',
  props.readonly ? 'is-readonly' : '',
])

function updateValue(nextValue) {
  emit('update:modelValue', nextValue)
  emit('input', nextValue)
}

function handleInput(event) {
  updateValue(String(event?.target?.value ?? ''))
}

function handleChange(event) {
  emit('change', String(event?.target?.value ?? ''))
}

function handleBlur(event) {
  emit('blur', event)
}

function handleFocus(event) {
  emit('focus', event)
}

function handleClear() {
  if (!showClear.value) {
    return
  }
  updateValue('')
  emit('change', '')
  emit('clear')
  controlRef.value?.focus()
}

function togglePasswordVisible() {
  if (!allowPasswordToggle.value || props.disabled) {
    return
  }
  passwordVisible.value = !passwordVisible.value
  controlRef.value?.focus()
}
</script>

<template>
  <div
    v-if="!isTextarea"
    v-bind="rootAttrs"
    :class="inputClasses"
  >
    <div class="el-input__wrapper">
      <input
        ref="controlRef"
        v-bind="controlAttrs"
        class="el-input__inner"
        :type="resolvedType"
        :name="name || undefined"
        :value="normalizedValue"
        :placeholder="placeholder || undefined"
        :maxlength="maxLength"
        :disabled="disabled"
        :readonly="readonly"
        @input="handleInput"
        @change="handleChange"
        @blur="handleBlur"
        @focus="handleFocus"
      >

      <span
        v-if="showClear || allowPasswordToggle"
        class="el-input__suffix"
      >
        <button
          v-if="showClear"
          type="button"
          class="ui-input__action ui-input__clear"
          @click.stop="handleClear"
        >
          x
        </button>
        <button
          v-if="allowPasswordToggle"
          type="button"
          class="ui-input__action ui-input__password-toggle"
          @click.stop="togglePasswordVisible"
        >
          {{ passwordVisible ? '隐藏' : '显示' }}
        </button>
      </span>
    </div>

    <div
      v-if="showWordLimitIndicator"
      class="el-input__count"
    >
      {{ wordCount }} / {{ maxLength }}
    </div>
  </div>

  <div
    v-else
    v-bind="rootAttrs"
    :class="textareaClasses"
  >
    <textarea
      ref="controlRef"
      v-bind="controlAttrs"
      class="el-textarea__inner"
      :name="name || undefined"
      :value="normalizedValue"
      :rows="rows"
      :maxlength="maxLength"
      :placeholder="placeholder || undefined"
      :disabled="disabled"
      :readonly="readonly"
      @input="handleInput"
      @change="handleChange"
      @blur="handleBlur"
      @focus="handleFocus"
    />

    <div
      v-if="showWordLimitIndicator"
      class="el-input__count el-input__count--textarea"
    >
      {{ wordCount }} / {{ maxLength }}
    </div>
  </div>
</template>

<style scoped>
.ui-input,
.ui-textarea {
  width: 100%;
}

.el-input__wrapper,
.el-textarea__inner {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 86%, white 14%);
  border-radius: 14px;
  background: color-mix(in srgb, var(--qb-surface-card) 88%, white 12%);
  color: var(--qb-text-primary);
  box-sizing: border-box;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.el-input__wrapper {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 0 14px;
}

.el-input__inner,
.el-textarea__inner {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  font: inherit;
}

.el-input__inner::placeholder,
.el-textarea__inner::placeholder {
  color: var(--qb-text-meta);
}

.el-textarea__inner {
  display: block;
  min-height: 112px;
  padding: 12px 14px;
  resize: vertical;
  line-height: 1.6;
}

.ui-input:not(.is-disabled):not(.is-readonly):focus-within .el-input__wrapper,
.ui-textarea:not(.is-disabled):not(.is-readonly):focus-within .el-textarea__inner {
  border-color: color-mix(in srgb, var(--qb-primary-student) 42%, white 58%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
}

.ui-input:not(.is-disabled):not(.is-readonly) .el-input__wrapper:hover,
.ui-textarea:not(.is-disabled):not(.is-readonly) .el-textarea__inner:hover {
  border-color: color-mix(in srgb, var(--qb-primary-student) 24%, white 76%);
}

.ui-input.is-disabled .el-input__wrapper,
.ui-textarea.is-disabled .el-textarea__inner,
.ui-input.is-readonly .el-input__wrapper,
.ui-textarea.is-readonly .el-textarea__inner {
  background: color-mix(in srgb, var(--qb-bg-muted) 78%, white 22%);
}

.ui-input.is-disabled,
.ui-textarea.is-disabled {
  opacity: 0.72;
}

.ui-input__action {
  border: 0;
  background: transparent;
  color: var(--qb-text-meta);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.ui-input__action:hover {
  color: var(--qb-primary-student);
}

.el-input__suffix {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-left: 10px;
  flex: 0 0 auto;
}

.el-input__count {
  margin-top: 6px;
  text-align: right;
  color: var(--qb-text-meta);
  font-size: 12px;
  line-height: 1.2;
}

.el-input__count--textarea {
  margin-top: 8px;
}
</style>
