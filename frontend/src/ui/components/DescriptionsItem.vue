<script setup>
import { computed, inject } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  span: {
    type: Number,
    default: 1,
  },
})

const descriptionsContext = inject('uiDescriptionsContext', computed(() => ({
  column: 3,
  border: false,
  size: 'default',
  direction: 'horizontal',
})))

const normalizedSpan = computed(() => {
  const candidate = Number(props.span || 1)
  if (!Number.isFinite(candidate) || candidate <= 0) {
    return 1
  }
  return Math.max(1, Math.floor(candidate))
})

const itemClasses = computed(() => [
  'ui-descriptions-item',
  'el-descriptions-item',
  descriptionsContext.value.border ? 'is-bordered' : '',
  descriptionsContext.value.direction === 'vertical' ? 'is-vertical' : '',
])

const itemStyle = computed(() => ({
  gridColumn: `span ${Math.min(normalizedSpan.value, descriptionsContext.value.column || 1)}`,
}))
</script>

<template>
  <div :class="itemClasses" :style="itemStyle">
    <div class="ui-descriptions-item__container">
      <div class="ui-descriptions-item__label el-descriptions-item__label">
        <slot name="label">
          {{ label }}
        </slot>
      </div>
      <div class="ui-descriptions-item__content el-descriptions-item__content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.ui-descriptions-item {
  min-width: 0;
}

.ui-descriptions-item__container {
  display: grid;
  grid-template-columns: minmax(88px, auto) minmax(0, 1fr);
  align-items: stretch;
  min-height: 42px;
  border-radius: inherit;
  overflow: hidden;
}

.ui-descriptions-item.is-bordered .ui-descriptions-item__container {
  border-right: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
}

.ui-descriptions-item__label,
.ui-descriptions-item__content {
  display: flex;
  align-items: center;
  min-width: 0;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.6;
  box-sizing: border-box;
}

.ui-descriptions-item__label {
  color: var(--qb-text-secondary);
  font-weight: 600;
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 48%, white 52%);
}

.ui-descriptions-item__content {
  color: var(--qb-text-primary);
  background: rgba(255, 255, 255, 0.92);
  word-break: break-word;
}
</style>
