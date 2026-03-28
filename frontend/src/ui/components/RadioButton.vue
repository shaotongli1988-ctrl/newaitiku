<script setup>
import { computed, inject } from 'vue'
import {
  isRadioChecked,
  radioGroupContextKey,
  shouldEmitRadioChange,
} from './radioShared'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean],
    default: undefined,
  },
  label: {
    type: [String, Number, Boolean],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const radioGroup = inject(radioGroupContextKey, null)

const mergedModelValue = computed(() => radioGroup?.modelValue?.value ?? props.modelValue)
const mergedDisabled = computed(() => Boolean(props.disabled || radioGroup?.disabled?.value))
const mergedName = computed(() => radioGroup?.name?.value || props.name || undefined)
const fillColor = computed(() => radioGroup?.fill?.value || 'var(--qb-primary-student)')
const textColor = computed(() => radioGroup?.textColor?.value || 'var(--qb-text-inverse)')
const isChecked = computed(() => isRadioChecked(mergedModelValue.value, props.label))

const buttonClasses = computed(() => [
  'ui-radio-button',
  'el-radio-button',
  isChecked.value ? 'is-active' : '',
  mergedDisabled.value ? 'is-disabled' : '',
])

const buttonVars = computed(() => ({
  '--ui-radio-button-fill': fillColor.value,
  '--ui-radio-button-text': textColor.value,
}))

function updateValue() {
  if (mergedDisabled.value) {
    return
  }

  if (!shouldEmitRadioChange(mergedModelValue.value, props.label)) {
    return
  }

  if (radioGroup) {
    radioGroup.changeValue(props.label)
  } else {
    emit('update:modelValue', props.label)
  }

  emit('change', props.label)
}
</script>

<template>
  <label :class="buttonClasses" :style="buttonVars">
    <input
      class="el-radio-button__original-radio"
      type="radio"
      :name="mergedName"
      :checked="isChecked"
      :disabled="mergedDisabled"
      @change="updateValue"
    >
    <span class="el-radio-button__inner">
      <slot />
    </span>
  </label>
</template>

<style scoped>
.ui-radio-button {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  margin-left: -1px;
  cursor: pointer;
}

.ui-radio-button:first-child {
  margin-left: 0;
}

.ui-radio-button.is-disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.el-radio-button__original-radio {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  pointer-events: none;
}

.el-radio-button__inner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 18px;
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 84%, white 16%);
  background: color-mix(in srgb, var(--qb-surface-card) 94%, white 6%);
  color: var(--qb-text-secondary);
  font-size: 14px;
  line-height: 1;
  white-space: nowrap;
  transition: border-color 180ms ease, background-color 180ms ease, color 180ms ease, box-shadow 180ms ease;
}

.ui-radio-button:first-child .el-radio-button__inner {
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
}

.ui-radio-button:last-child .el-radio-button__inner {
  border-top-right-radius: 12px;
  border-bottom-right-radius: 12px;
}

.ui-radio-button:not(.is-disabled):hover .el-radio-button__inner {
  color: var(--qb-text-primary);
  border-color: color-mix(in srgb, var(--qb-primary-student) 40%, white 60%);
}

.ui-radio-button.is-active .el-radio-button__inner {
  position: relative;
  z-index: 1;
  border-color: var(--ui-radio-button-fill);
  background: var(--ui-radio-button-fill);
  color: var(--ui-radio-button-text);
  box-shadow: 0 12px 24px -20px color-mix(in srgb, var(--ui-radio-button-fill) 65%, transparent 35%);
}
</style>
