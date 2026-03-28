<script setup>
import { computed } from 'vue'

const props = defineProps({
  animated: {
    type: Boolean,
    default: false,
  },
  count: {
    type: Number,
    default: 1,
  },
  rows: {
    type: Number,
    default: 3,
  },
  loading: {
    type: Boolean,
    default: true,
  },
  throttle: {
    type: Number,
    default: 0,
  },
})

const normalizedCount = computed(() => Math.max(1, Number(props.count) || 1))
const normalizedRows = computed(() => Math.max(1, Number(props.rows) || 1))
const shouldRenderSkeleton = computed(() => props.loading)

function resolveRowWidth(index, total) {
  if (total <= 1) {
    return '100%'
  }
  if (index === total - 1) {
    return '62%'
  }
  if (index === 0 && total >= 4) {
    return '84%'
  }
  return '100%'
}
</script>

<template>
  <template v-if="!shouldRenderSkeleton">
    <slot />
  </template>
  <div
    v-else
    class="ui-skeleton el-skeleton"
    :class="{ 'is-animated': animated }"
    :data-throttle="throttle || undefined"
  >
    <template v-for="itemIndex in normalizedCount" :key="`skeleton-${itemIndex}`">
      <slot name="template">
        <div class="ui-skeleton__template el-skeleton__template">
          <span
            v-for="rowIndex in normalizedRows"
            :key="`row-${itemIndex}-${rowIndex}`"
            class="ui-skeleton-item ui-skeleton-item--text el-skeleton__item"
            :style="{ width: resolveRowWidth(rowIndex - 1, normalizedRows) }"
            aria-hidden="true"
          />
        </div>
      </slot>
    </template>
  </div>
</template>

<style scoped>
.ui-skeleton,
.ui-skeleton__template {
  display: grid;
  gap: 12px;
  width: 100%;
}

.ui-skeleton-item {
  position: relative;
  display: block;
  overflow: hidden;
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

.ui-skeleton.is-animated :deep(.ui-skeleton-item)::after,
.ui-skeleton.is-animated :deep(.el-skeleton__item)::after {
  opacity: 1;
  animation: ui-skeleton-wave 1.4s ease-in-out infinite;
}

.ui-skeleton-item--text {
  height: 16px;
}

@keyframes ui-skeleton-wave {
  100% {
    transform: translateX(100%);
  }
}
</style>
