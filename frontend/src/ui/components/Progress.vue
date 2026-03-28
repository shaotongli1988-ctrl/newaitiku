<script setup>
import { computed } from 'vue'

const props = defineProps({
  percentage: {
    type: Number,
    default: 0,
  },
  status: {
    type: String,
    default: '',
  },
  strokeWidth: {
    type: Number,
    default: 6,
  },
  color: {
    type: [String, Function, Array],
    default: undefined,
  },
  format: {
    type: Function,
    default: undefined,
  },
})

const normalizedPercentage = computed(() => {
  const candidate = Number(props.percentage || 0)
  if (!Number.isFinite(candidate)) {
    return 0
  }
  return Math.min(100, Math.max(0, candidate))
})

const normalizedStatus = computed(() => {
  const candidate = String(props.status || '').trim()
  if (['success', 'exception', 'warning'].includes(candidate)) {
    return candidate
  }
  return ''
})

const normalizedStrokeWidth = computed(() => {
  const candidate = Number(props.strokeWidth || 6)
  if (!Number.isFinite(candidate) || candidate <= 0) {
    return 6
  }
  return candidate
})

function resolveColorByArray(colorStops, percentage) {
  return [...colorStops]
    .filter((item) => item && typeof item === 'object')
    .sort((left, right) => Number(left.percentage || 0) - Number(right.percentage || 0))
    .find((item) => percentage <= Number(item.percentage || 0))?.color
}

const trackColor = computed(() => {
  const percentage = normalizedPercentage.value

  if (typeof props.color === 'function') {
    return props.color(percentage)
  }

  if (Array.isArray(props.color)) {
    const matched = resolveColorByArray(props.color, percentage)
    if (matched) {
      return matched
    }
  }

  if (typeof props.color === 'string' && props.color.trim()) {
    return props.color
  }

  if (normalizedStatus.value === 'success') {
    return 'var(--qb-success)'
  }

  if (normalizedStatus.value === 'exception') {
    return 'var(--qb-danger)'
  }

  if (normalizedStatus.value === 'warning') {
    return 'var(--qb-warning)'
  }

  return 'var(--qb-primary-student)'
})

const label = computed(() => {
  if (typeof props.format === 'function') {
    return String(props.format(normalizedPercentage.value))
  }
  return `${Math.round(normalizedPercentage.value)}%`
})

const progressClasses = computed(() => [
  'ui-progress',
  'el-progress',
  'el-progress--line',
  normalizedStatus.value ? `is-${normalizedStatus.value}` : '',
])

const trackStyle = computed(() => ({
  '--ui-progress-height': `${normalizedStrokeWidth.value}px`,
  '--ui-progress-color': trackColor.value,
}))

const barStyle = computed(() => ({
  width: `${normalizedPercentage.value}%`,
}))
</script>

<template>
  <div :class="progressClasses" :style="trackStyle" role="progressbar" :aria-valuenow="normalizedPercentage" aria-valuemin="0" aria-valuemax="100">
    <div class="ui-progress-bar el-progress-bar">
      <div class="ui-progress-bar__outer el-progress-bar__outer">
        <div class="ui-progress-bar__inner el-progress-bar__inner" :style="barStyle">
          <span class="ui-progress-bar__inner-text el-progress-bar__innerText">{{ label }}</span>
        </div>
      </div>
    </div>

    <div class="ui-progress__text el-progress__text">
      {{ label }}
    </div>
  </div>
</template>

<style scoped>
.ui-progress {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-width: 0;
  --ui-progress-height: 6px;
  --ui-progress-color: var(--qb-primary-student);
}

.ui-progress-bar {
  min-width: 0;
}

.ui-progress-bar__outer {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: var(--ui-progress-height);
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.76), rgba(241, 245, 249, 0.92)),
    rgba(148, 163, 184, 0.14);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12);
}

.ui-progress-bar__inner {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: max(var(--ui-progress-height), 2px);
  height: 100%;
  overflow: hidden;
  border-radius: inherit;
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--ui-progress-color) 86%, white 14%), var(--ui-progress-color));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    0 6px 14px color-mix(in srgb, var(--ui-progress-color) 28%, transparent);
  transition:
    width 220ms ease,
    background-color 220ms ease;
}

.ui-progress-bar__inner-text {
  display: none;
}

.ui-progress__text {
  flex: 0 0 auto;
  color: var(--qb-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.ui-progress.is-success .ui-progress__text {
  color: color-mix(in srgb, var(--qb-success) 88%, black 12%);
}

.ui-progress.is-exception .ui-progress__text {
  color: color-mix(in srgb, var(--qb-danger) 88%, black 12%);
}

.ui-progress.is-warning .ui-progress__text {
  color: color-mix(in srgb, var(--qb-warning) 88%, black 12%);
}
</style>
