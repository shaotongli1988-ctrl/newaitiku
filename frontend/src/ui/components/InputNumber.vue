<script setup>
import { computed, ref, watch } from 'vue'
import {
  formatInputNumberValue,
  normalizeInputNumberValue,
  resolveInputNumberPrecision,
  stepInputNumber,
  toFiniteNumber,
} from './inputNumberShared'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: undefined,
  },
  min: {
    type: Number,
    default: undefined,
  },
  max: {
    type: Number,
    default: undefined,
  },
  step: {
    type: Number,
    default: 1,
  },
  precision: {
    type: Number,
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  controlsPosition: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'blur', 'focus'])

const isFocused = ref(false)
const effectivePrecision = computed(() =>
  resolveInputNumberPrecision(props.step, props.precision),
)

const normalizedModelValue = computed(() =>
  normalizeInputNumberValue(props.modelValue, {
    min: props.min,
    max: props.max,
    precision: effectivePrecision.value,
  }),
)

const draftValue = ref(formatInputNumberValue(normalizedModelValue.value, effectivePrecision.value))

watch(
  () => [
    props.modelValue,
    props.min,
    props.max,
    props.step,
    props.precision,
  ],
  () => {
    if (isFocused.value) {
      return
    }
    draftValue.value = formatInputNumberValue(
      normalizedModelValue.value,
      effectivePrecision.value,
    )
  },
  { immediate: true },
)

const inputNumberClasses = computed(() => [
  'ui-input-number',
  'el-input-number',
  props.disabled ? 'is-disabled' : '',
  props.controlsPosition === 'right' ? 'is-controls-right' : '',
])

const canDecrease = computed(() => {
  if (props.disabled) {
    return false
  }
  const currentValue = normalizedModelValue.value
  if (currentValue === undefined) {
    return true
  }
  const minValue = toFiniteNumber(props.min)
  return minValue === undefined || currentValue > minValue
})

const canIncrease = computed(() => {
  if (props.disabled) {
    return false
  }
  const currentValue = normalizedModelValue.value
  if (currentValue === undefined) {
    return true
  }
  const maxValue = toFiniteNumber(props.max)
  return maxValue === undefined || currentValue < maxValue
})

function commitValue(nextValue, { emitChange = true } = {}) {
  const normalizedValue = normalizeInputNumberValue(nextValue, {
    min: props.min,
    max: props.max,
    precision: effectivePrecision.value,
  })

  if (normalizedValue === undefined) {
    draftValue.value = formatInputNumberValue(
      normalizedModelValue.value,
      effectivePrecision.value,
    )
    return
  }

  const previousValue = normalizedModelValue.value
  draftValue.value = formatInputNumberValue(normalizedValue, effectivePrecision.value)
  emit('update:modelValue', normalizedValue)

  if (emitChange && normalizedValue !== previousValue) {
    emit('change', normalizedValue)
  }
}

function stepBy(direction) {
  if (props.disabled) {
    return
  }

  const nextValue = stepInputNumber(draftValue.value || props.modelValue, direction, {
    min: props.min,
    max: props.max,
    step: props.step,
    precision: props.precision,
  })

  commitValue(nextValue)
}

function handleInput(event) {
  draftValue.value = String(event?.target?.value ?? '')
}

function handleBlur(event) {
  isFocused.value = false
  commitValue(draftValue.value)
  emit('blur', event)
}

function handleFocus(event) {
  isFocused.value = true
  emit('focus', event)
}

function handleKeydown(event) {
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    stepBy(1)
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    stepBy(-1)
    return
  }

  if (event.key === 'Enter') {
    event.preventDefault()
    commitValue(draftValue.value)
  }
}
</script>

<template>
  <div :class="inputNumberClasses">
    <button
      v-if="controlsPosition !== 'right'"
      type="button"
      class="el-input-number__decrease"
      :class="{ 'is-disabled': !canDecrease }"
      :disabled="!canDecrease"
      @click="stepBy(-1)"
    >
      -
    </button>

    <div class="el-input">
      <div class="el-input__wrapper">
        <input
          class="el-input__inner"
          type="text"
          inputmode="decimal"
          :name="name || undefined"
          :disabled="disabled"
          :placeholder="placeholder || undefined"
          :value="draftValue"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
          @keydown="handleKeydown"
        >
      </div>
    </div>

    <template v-if="controlsPosition === 'right'">
      <button
        type="button"
        class="el-input-number__increase"
        :class="{ 'is-disabled': !canIncrease }"
        :disabled="!canIncrease"
        @click="stepBy(1)"
      >
        +
      </button>
      <button
        type="button"
        class="el-input-number__decrease"
        :class="{ 'is-disabled': !canDecrease }"
        :disabled="!canDecrease"
        @click="stepBy(-1)"
      >
        -
      </button>
    </template>

    <button
      v-else
      type="button"
      class="el-input-number__increase"
      :class="{ 'is-disabled': !canIncrease }"
      :disabled="!canIncrease"
      @click="stepBy(1)"
    >
      +
    </button>
  </div>
</template>

<style scoped>
.ui-input-number {
  position: relative;
  display: inline-grid;
  grid-template-columns: 36px minmax(88px, 1fr) 36px;
  align-items: stretch;
  min-width: 132px;
  width: 100%;
  border: 1px solid var(--qb-border-muted);
  border-radius: 14px;
  overflow: hidden;
  background: color-mix(in srgb, var(--qb-surface-card) 96%, white 4%);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.ui-input-number.is-controls-right {
  grid-template-columns: minmax(96px, 1fr) 32px;
  grid-template-rows: 1fr 1fr;
}

.ui-input-number.is-disabled {
  opacity: 0.62;
}

.ui-input-number:not(.is-disabled):focus-within {
  border-color: color-mix(in srgb, var(--qb-primary-student) 56%, white 44%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 68%, white 32%);
}

.el-input {
  min-width: 0;
}

.ui-input-number:not(.is-controls-right) .el-input {
  grid-column: 2;
}

.ui-input-number.is-controls-right .el-input {
  grid-row: 1 / span 2;
  grid-column: 1;
}

.el-input__wrapper {
  display: flex;
  align-items: center;
  height: 100%;
  background: transparent;
}

.el-input__inner {
  width: 100%;
  height: 100%;
  min-height: 38px;
  padding: 0 12px;
  border: 0;
  background: transparent;
  color: var(--qb-text-primary);
  font: inherit;
  text-align: center;
  outline: none;
}

.el-input__inner::placeholder {
  color: var(--qb-text-subtle-3);
}

.el-input-number__decrease,
.el-input-number__increase {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: color-mix(in srgb, var(--qb-surface-muted) 82%, white 18%);
  color: var(--qb-text-secondary);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 180ms ease, color 180ms ease;
}

.ui-input-number:not(.is-disabled) .el-input-number__decrease:not(.is-disabled):hover,
.ui-input-number:not(.is-disabled) .el-input-number__increase:not(.is-disabled):hover {
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 70%, white 30%);
  color: var(--qb-text-primary);
}

.ui-input-number.is-controls-right .el-input-number__increase {
  grid-column: 2;
  grid-row: 1;
  border-left: 1px solid color-mix(in srgb, var(--qb-border-muted) 76%, white 24%);
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-muted) 76%, white 24%);
}

.ui-input-number.is-controls-right .el-input-number__decrease {
  grid-column: 2;
  grid-row: 2;
  border-left: 1px solid color-mix(in srgb, var(--qb-border-muted) 76%, white 24%);
}

.ui-input-number:not(.is-controls-right) .el-input-number__decrease {
  border-right: 1px solid color-mix(in srgb, var(--qb-border-muted) 76%, white 24%);
}

.ui-input-number:not(.is-controls-right) .el-input-number__increase {
  border-left: 1px solid color-mix(in srgb, var(--qb-border-muted) 76%, white 24%);
}

.el-input-number__decrease.is-disabled,
.el-input-number__increase.is-disabled {
  cursor: not-allowed;
  opacity: 0.46;
}
</style>
