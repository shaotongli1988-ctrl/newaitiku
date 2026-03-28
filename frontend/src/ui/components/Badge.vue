<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [String, Number],
    default: '',
  },
  hidden: {
    type: Boolean,
    default: false,
  },
  isDot: {
    type: Boolean,
    default: false,
  },
  max: {
    type: Number,
    default: undefined,
  },
  type: {
    type: String,
    default: 'danger',
  },
})

const normalizedType = computed(() => {
  const candidate = String(props.type || 'danger').trim()
  if (['primary', 'success', 'warning', 'info', 'danger'].includes(candidate)) {
    return candidate
  }
  return 'danger'
})

const displayValue = computed(() => {
  if (props.isDot) {
    return ''
  }

  const numericValue = Number(props.value)
  if (Number.isFinite(numericValue) && Number.isFinite(props.max) && numericValue > props.max) {
    return `${props.max}+`
  }

  return String(props.value ?? '')
})

const isVisible = computed(() => {
  if (props.hidden) {
    return false
  }
  if (props.isDot) {
    return true
  }
  return Boolean(displayValue.value)
})

const paletteMap = {
  primary: 'var(--qb-primary-student)',
  success: 'var(--qb-success)',
  warning: 'var(--qb-warning)',
  info: 'var(--qb-text-secondary)',
  danger: 'var(--qb-danger)',
}

const badgeStyle = computed(() => ({
  '--ui-badge-color': paletteMap[normalizedType.value] || paletteMap.danger,
}))
</script>

<template>
  <span class="ui-badge el-badge" :style="badgeStyle">
    <slot />
    <sup
      v-if="isVisible"
      class="ui-badge__content el-badge__content"
      :class="[
        `el-badge__content--${normalizedType}`,
        { 'is-fixed': true, 'is-dot': isDot },
      ]"
    >
      <template v-if="!isDot">{{ displayValue }}</template>
    </sup>
  </span>
</template>

<style scoped>
.ui-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}

.ui-badge__content {
  position: absolute;
  top: 0;
  right: 0;
  transform: translate(58%, -42%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border: 2px solid white;
  border-radius: 999px;
  background: var(--ui-badge-color);
  color: var(--qb-text-inverse);
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  box-sizing: border-box;
  box-shadow: 0 8px 18px color-mix(in srgb, var(--ui-badge-color) 20%, transparent);
}

.ui-badge__content.is-dot {
  min-width: 10px;
  width: 10px;
  height: 10px;
  padding: 0;
}
</style>
