<script setup>
import { computed } from 'vue'
import {
  normalizeSliderStep,
  normalizeSliderValue,
  resolveSliderFillPercent,
} from './sliderShared'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  max: {
    type: [String, Number],
    default: 100,
  },
  min: {
    type: [String, Number],
    default: 0,
  },
  modelValue: {
    type: [String, Number],
    default: 0,
  },
  showInput: {
    type: Boolean,
    default: false,
  },
  step: {
    type: [String, Number],
    default: 1,
  },
})

const emit = defineEmits(['update:modelValue', 'input', 'change'])

const normalizedMin = computed(() => Number(props.min))
const normalizedMax = computed(() => Number(props.max))
const normalizedStep = computed(() => normalizeSliderStep(props.step))
const currentValue = computed(() => normalizeSliderValue(props.modelValue, {
  min: normalizedMin.value,
  max: normalizedMax.value,
  step: normalizedStep.value,
}))
const fillPercent = computed(() => resolveSliderFillPercent(
  currentValue.value,
  normalizedMin.value,
  normalizedMax.value,
))

function emitValue(nextRawValue, emitChange = false) {
  const nextValue = normalizeSliderValue(nextRawValue, {
    min: normalizedMin.value,
    max: normalizedMax.value,
    step: normalizedStep.value,
  })
  emit('update:modelValue', nextValue)
  emit('input', nextValue)
  if (emitChange) {
    emit('change', nextValue)
  }
}

function handleRangeInput(event) {
  emitValue(event?.target?.value, false)
}

function handleRangeChange(event) {
  emitValue(event?.target?.value, true)
}

function handleInputNumber(event) {
  emitValue(event?.target?.value, true)
}
</script>

<template>
  <div class="ui-slider el-slider" :class="{ 'is-disabled': disabled }">
    <div class="el-slider__runway" :style="{ '--ui-slider-fill': `${fillPercent}%` }">
      <div class="el-slider__bar" />
      <input
        class="ui-slider__native"
        type="range"
        :min="normalizedMin"
        :max="normalizedMax"
        :step="normalizedStep"
        :value="currentValue"
        :disabled="disabled"
        @input="handleRangeInput"
        @change="handleRangeChange"
      >
    </div>

    <input
      v-if="showInput"
      class="ui-slider__input"
      type="number"
      :min="normalizedMin"
      :max="normalizedMax"
      :step="normalizedStep"
      :value="currentValue"
      :disabled="disabled"
      @change="handleInputNumber"
    >
  </div>
</template>

<style scoped>
.ui-slider {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.ui-slider.is-disabled {
  opacity: 0.6;
}

.el-slider__runway {
  position: relative;
  flex: 1 1 auto;
  height: 8px;
  border-radius: 999px;
  background:
    linear-gradient(
      90deg,
      var(--qb-primary-student) 0,
      var(--qb-primary-student) var(--ui-slider-fill, 0%),
      rgba(203, 213, 225, 0.95) var(--ui-slider-fill, 0%),
      rgba(203, 213, 225, 0.95) 100%
    );
}

.el-slider__bar {
  display: none;
}

.ui-slider__native {
  position: absolute;
  inset: -6px 0;
  width: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.ui-slider__input {
  width: 72px;
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 12px;
  background: var(--qb-surface-strong);
  color: var(--qb-text-primary);
  font-size: 14px;
}
</style>
