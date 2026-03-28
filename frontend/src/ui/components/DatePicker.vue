<script setup>
import { computed } from 'vue'
import {
  formatDatePickerOutput,
  normalizeDatePickerInputValue,
  resolveDatePickerInputType,
} from './datePickerShared'

const props = defineProps({
  modelValue: {
    type: [String, Number, Date],
    default: '',
  },
  type: {
    type: String,
    default: 'date',
  },
  valueFormat: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'clear'])

const inputType = computed(() => resolveDatePickerInputType(props.type))
const inputValue = computed(() => normalizeDatePickerInputValue(props.modelValue, {
  type: props.type,
}))
const showClear = computed(() => props.clearable && !props.disabled && Boolean(inputValue.value))
const pickerClasses = computed(() => [
  'ui-date-picker',
  'el-date-editor',
  'el-input',
  props.disabled ? 'is-disabled' : '',
])

function updateValue(nextInputValue) {
  const nextValue = formatDatePickerOutput(nextInputValue, {
    type: props.type,
    valueFormat: props.valueFormat,
  })
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

function handleInput(event) {
  updateValue(event?.target?.value || '')
}

function clearValue() {
  if (!showClear.value) {
    return
  }
  emit('update:modelValue', '')
  emit('change', '')
  emit('clear')
}
</script>

<template>
  <div :class="pickerClasses">
    <div class="el-input__wrapper">
      <input
        class="el-input__inner"
        :type="inputType"
        :value="inputValue"
        :disabled="disabled"
        :placeholder="placeholder || undefined"
        :step="inputType === 'datetime-local' ? 1 : undefined"
        @input="handleInput"
        @change="handleInput"
      >
      <button
        v-if="showClear"
        type="button"
        class="ui-date-picker__clear"
        aria-label="清除日期"
        @click="clearValue"
      >
        ×
      </button>
    </div>
  </div>
</template>

<style scoped>
.ui-date-picker {
  display: inline-flex;
  width: 100%;
  min-width: 0;
}

.ui-date-picker.is-disabled {
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

.ui-date-picker:not(.is-disabled):focus-within .el-input__wrapper {
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

.ui-date-picker__clear {
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--qb-text-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}
</style>
