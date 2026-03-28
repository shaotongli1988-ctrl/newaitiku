<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  direction: {
    type: String,
    default: 'horizontal',
  },
  contentPosition: {
    type: String,
    default: 'center',
  },
  borderStyle: {
    type: String,
    default: 'solid',
  },
})

const slots = useSlots()

const normalizedDirection = computed(() => (
  String(props.direction || 'horizontal').trim() === 'vertical' ? 'vertical' : 'horizontal'
))

const normalizedContentPosition = computed(() => {
  const candidate = String(props.contentPosition || 'center').trim()
  if (['left', 'center', 'right'].includes(candidate)) {
    return candidate
  }
  return 'center'
})

const normalizedBorderStyle = computed(() => {
  const candidate = String(props.borderStyle || 'solid').trim()
  if (['solid', 'dashed', 'dotted', 'double'].includes(candidate)) {
    return candidate
  }
  return 'solid'
})

const hasContent = computed(() => Boolean(slots.default))
</script>

<template>
  <div
    class="ui-divider el-divider"
    :class="[
      `el-divider--${normalizedDirection}`,
      normalizedDirection === 'horizontal' ? `is-${normalizedContentPosition}` : '',
    ]"
    :style="{ '--ui-divider-border-style': normalizedBorderStyle }"
    role="separator"
    :aria-orientation="normalizedDirection"
  >
    <template v-if="normalizedDirection === 'vertical'"></template>
    <template v-else-if="hasContent">
      <span class="ui-divider__text el-divider__text" :class="`is-${normalizedContentPosition}`">
        <slot />
      </span>
    </template>
  </div>
</template>

<style scoped>
.ui-divider {
  --ui-divider-color: color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
  position: relative;
  box-sizing: border-box;
}

.ui-divider--horizontal {
  display: flex;
  align-items: center;
  width: 100%;
  margin: 28px 0 22px;
  color: var(--qb-text-secondary-strong);
  font-size: 13px;
  letter-spacing: 0.02em;
}

.ui-divider--horizontal::before,
.ui-divider--horizontal::after {
  content: '';
  display: block;
  flex: 1 1 0;
  border-top: 1px var(--ui-divider-border-style) var(--ui-divider-color);
}

.ui-divider--horizontal.is-left::before {
  flex: 0 0 28px;
}

.ui-divider--horizontal.is-right::after {
  flex: 0 0 28px;
}

.ui-divider__text {
  flex: 0 0 auto;
  padding: 0 14px;
  font-weight: 700;
  color: var(--qb-text-secondary-strong);
}

.ui-divider--vertical {
  display: inline-block;
  width: 1px;
  min-height: 1em;
  margin: 0 10px;
  vertical-align: middle;
  border-left: 1px var(--ui-divider-border-style) var(--ui-divider-color);
}
</style>
