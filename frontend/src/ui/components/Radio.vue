<script setup>
import { computed, inject } from 'vue'
import {
  isRadioChecked,
  normalizeRadioSize,
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
  border: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const radioGroup = inject(radioGroupContextKey, null)

const mergedModelValue = computed(() => radioGroup?.modelValue?.value ?? props.modelValue)
const mergedDisabled = computed(() => Boolean(props.disabled || radioGroup?.disabled?.value))
const mergedName = computed(() => radioGroup?.name?.value || props.name || undefined)
const mergedSize = computed(() => normalizeRadioSize(props.size || radioGroup?.size?.value))
const isChecked = computed(() => isRadioChecked(mergedModelValue.value, props.label))

const radioClasses = computed(() => [
  'ui-radio',
  'el-radio',
  isChecked.value ? 'is-checked' : '',
  mergedDisabled.value ? 'is-disabled' : '',
  props.border ? 'is-bordered' : '',
  mergedSize.value ? `el-radio--${mergedSize.value}` : '',
])

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
  <label :class="radioClasses">
    <span class="el-radio__input" :class="{ 'is-checked': isChecked, 'is-disabled': mergedDisabled }">
      <span class="el-radio__inner" />
      <input
        class="el-radio__original"
        type="radio"
        :name="mergedName"
        :checked="isChecked"
        :disabled="mergedDisabled"
        :aria-checked="String(isChecked)"
        @change="updateValue"
      >
    </span>

    <span v-if="$slots.default" class="el-radio__label">
      <slot />
    </span>
  </label>
</template>

<style scoped>
.ui-radio {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-right: 18px;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.45;
  cursor: pointer;
  user-select: none;
}

.ui-radio.is-disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.el-radio__input {
  position: relative;
  flex: 0 0 auto;
  display: inline-flex;
  width: 18px;
  height: 18px;
}

.el-radio__inner {
  position: relative;
  width: 18px;
  height: 18px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 999px;
  background: var(--qb-surface-strong);
  transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.el-radio__inner::after {
  content: '';
  position: absolute;
  inset: 4px;
  border-radius: inherit;
  background: var(--qb-primary-student);
  opacity: 0;
  transform: scale(0.4);
  transition: opacity 160ms ease, transform 160ms ease;
}

.el-radio__input.is-checked .el-radio__inner {
  border-color: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
}

.el-radio__input.is-checked .el-radio__inner::after {
  opacity: 1;
  transform: scale(1);
}

.el-radio__original {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: inherit;
}

.ui-radio:not(.is-disabled):hover .el-radio__inner {
  border-color: color-mix(in srgb, var(--qb-primary-student) 56%, white 44%);
}

.el-radio__label {
  min-width: 0;
}

.ui-radio.is-bordered {
  width: 100%;
  min-height: 56px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--qb-border-muted) 88%, white 12%);
  border-radius: 16px;
  background: color-mix(in srgb, var(--qb-surface-card) 92%, white 8%);
  transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.ui-radio.is-bordered.is-checked {
  border-color: color-mix(in srgb, var(--qb-primary-student) 72%, white 28%);
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 88%, white 12%);
  box-shadow: 0 14px 30px -24px color-mix(in srgb, var(--qb-primary-student) 40%, transparent 60%);
}

.ui-radio.el-radio--large {
  font-size: 15px;
}

.ui-radio.el-radio--small {
  font-size: 13px;
}
</style>
