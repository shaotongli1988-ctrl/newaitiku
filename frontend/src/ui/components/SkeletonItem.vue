<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'text',
  },
})

const normalizedVariant = computed(() => {
  const candidate = String(props.variant || '').trim().toLowerCase()
  if (candidate === 'p') {
    return 'text'
  }
  if (['text', 'h1', 'rect', 'circle'].includes(candidate)) {
    return candidate
  }
  return 'text'
})
</script>

<template>
  <span
    class="ui-skeleton-item el-skeleton__item"
    :class="[
      `ui-skeleton-item--${normalizedVariant}`,
      normalizedVariant === 'circle' ? 'is-circle' : '',
    ]"
    aria-hidden="true"
  />
</template>

<style scoped>
.ui-skeleton-item {
  position: relative;
  display: block;
  overflow: hidden;
  width: 100%;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(203, 213, 225, 0.38), rgba(226, 232, 240, 0.72));
}

.ui-skeleton-item::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.72), transparent);
  opacity: 0;
  transform: translateX(-100%);
}

:global(.is-animated) .ui-skeleton-item::after,
:global(.is-animated) .el-skeleton__item::after {
  opacity: 1;
  animation: ui-skeleton-wave 1.4s ease-in-out infinite;
}

.ui-skeleton-item--text {
  height: 16px;
}

.ui-skeleton-item--h1 {
  height: 28px;
  border-radius: 18px;
}

.ui-skeleton-item--rect {
  min-height: 84px;
  border-radius: 18px;
}

.ui-skeleton-item--circle,
.ui-skeleton-item.is-circle {
  aspect-ratio: 1 / 1;
  border-radius: 999px;
}

@keyframes ui-skeleton-wave {
  100% {
    transform: translateX(100%);
  }
}
</style>
