<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Boolean, String, Number, Array],
    default: false,
  },
  label: {
    type: [String, Number, Boolean, Object],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  indeterminate: {
    type: Boolean,
    default: false,
  },
  trueLabel: {
    type: [String, Number, Boolean],
    default: true,
  },
  falseLabel: {
    type: [String, Number, Boolean],
    default: false,
  },
  checked: {
    type: Boolean,
    default: undefined,
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

function isArrayModel() {
  return Array.isArray(props.modelValue) && props.label !== undefined
}

const isChecked = computed(() => {
  if (typeof props.checked === 'boolean') {
    return props.checked
  }
  if (isArrayModel()) {
    return props.modelValue.includes(props.label)
  }
  return props.modelValue === props.trueLabel || props.modelValue === true
})

const checkboxClasses = computed(() => [
  'ui-checkbox',
  'el-checkbox',
  isChecked.value ? 'is-checked' : '',
  props.disabled ? 'is-disabled' : '',
  props.indeterminate ? 'is-indeterminate' : '',
])

function handleChange(event) {
  if (props.disabled) {
    return
  }

  const checked = Boolean(event?.target?.checked)
  let nextValue

  if (isArrayModel()) {
    const nextItems = [...props.modelValue]
    const existingIndex = nextItems.findIndex((item) => item === props.label)
    if (checked && existingIndex < 0) {
      nextItems.push(props.label)
    }
    if (!checked && existingIndex >= 0) {
      nextItems.splice(existingIndex, 1)
    }
    nextValue = nextItems
  } else {
    nextValue = checked ? props.trueLabel : props.falseLabel
  }

  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}
</script>

<template>
  <label :class="checkboxClasses">
    <span class="el-checkbox__input" :class="{ 'is-checked': isChecked, 'is-disabled': disabled, 'is-indeterminate': indeterminate }">
      <span class="el-checkbox__inner" />
      <input
        class="el-checkbox__original"
        type="checkbox"
        :name="name || undefined"
        :checked="isChecked"
        :disabled="disabled"
        :aria-checked="indeterminate ? 'mixed' : String(isChecked)"
        @change="handleChange"
      >
    </span>

    <span v-if="$slots.default" class="el-checkbox__label">
      <slot />
    </span>
  </label>
</template>

<style scoped>
.ui-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.4;
  cursor: pointer;
  user-select: none;
}

.ui-checkbox.is-disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.el-checkbox__input {
  position: relative;
  flex: 0 0 auto;
  display: inline-flex;
  width: 18px;
  height: 18px;
}

.el-checkbox__inner {
  position: relative;
  width: 18px;
  height: 18px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 6px;
  background: var(--qb-surface-strong);
  transition: border-color 180ms ease, background-color 180ms ease, box-shadow 180ms ease;
}

.el-checkbox__input.is-checked .el-checkbox__inner,
.el-checkbox__input.is-indeterminate .el-checkbox__inner {
  border-color: var(--qb-primary-student);
  background: var(--qb-primary-student);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
}

.el-checkbox__inner::after {
  content: '';
  position: absolute;
  inset: 3px 6px 4px 5px;
  border: solid var(--qb-text-inverse);
  border-width: 0 2px 2px 0;
  opacity: 0;
  transform: rotate(45deg) scale(0.8);
  transition: opacity 160ms ease, transform 160ms ease;
}

.el-checkbox__input.is-checked .el-checkbox__inner::after {
  opacity: 1;
  transform: rotate(45deg) scale(1);
}

.el-checkbox__input.is-indeterminate .el-checkbox__inner::after {
  inset: 7px 4px auto;
  height: 2px;
  border: 0;
  background: var(--qb-text-inverse);
  opacity: 1;
  transform: none;
}

.el-checkbox__original {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: inherit;
}

.ui-checkbox:not(.is-disabled):hover .el-checkbox__inner {
  border-color: color-mix(in srgb, var(--qb-primary-student) 56%, white 44%);
}

.el-checkbox__label {
  min-width: 0;
}
</style>
