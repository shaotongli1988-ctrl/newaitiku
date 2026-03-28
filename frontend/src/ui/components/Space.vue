<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: [String, Number, Array],
    default: 'small',
  },
  direction: {
    type: String,
    default: 'horizontal',
  },
  wrap: {
    type: Boolean,
    default: false,
  },
  alignment: {
    type: String,
    default: 'center',
  },
})

function normalizeGap(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `${value}px`
  }

  const candidate = String(value || '').trim()
  if (!candidate) {
    return '8px'
  }

  if (['small', 'default', 'large'].includes(candidate)) {
    return {
      small: '8px',
      default: '12px',
      large: '16px',
    }[candidate]
  }

  return /^\d+(\.\d+)?$/.test(candidate) ? `${candidate}px` : candidate
}

const horizontalGap = computed(() => {
  if (Array.isArray(props.size)) {
    return normalizeGap(props.size[0])
  }
  return normalizeGap(props.size)
})

const verticalGap = computed(() => {
  if (Array.isArray(props.size)) {
    return normalizeGap(props.size[1] ?? props.size[0])
  }
  return normalizeGap(props.size)
})

const normalizedDirection = computed(() => (
  String(props.direction || 'horizontal').trim() === 'vertical' ? 'vertical' : 'horizontal'
))

const normalizedAlignment = computed(() => {
  const candidate = String(props.alignment || 'center').trim()
  if (['start', 'end', 'center', 'baseline', 'stretch'].includes(candidate)) {
    return candidate
  }
  return 'center'
})

const spaceStyle = computed(() => ({
  '--ui-space-column-gap': horizontalGap.value,
  '--ui-space-row-gap': verticalGap.value,
}))
</script>

<template>
  <div
    class="ui-space el-space"
    :class="[
      `el-space--${normalizedDirection}`,
      { 'el-space--wrap': wrap },
    ]"
    :style="spaceStyle"
  >
    <slot />
  </div>
</template>

<style scoped>
.ui-space {
  display: inline-flex;
  flex-wrap: nowrap;
  align-items: v-bind(normalizedAlignment);
  gap: var(--ui-space-row-gap) var(--ui-space-column-gap);
}

.ui-space.el-space--vertical {
  flex-direction: column;
  align-items: stretch;
}

.ui-space.el-space--wrap {
  flex-wrap: wrap;
}
</style>
