<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  header: {
    type: String,
    default: '',
  },
  footer: {
    type: String,
    default: '',
  },
  shadow: {
    type: String,
    default: 'always',
  },
  bodyStyle: {
    type: [Object, Array, String],
    default: undefined,
  },
  bodyClass: {
    type: [String, Array, Object],
    default: '',
  },
})

const slots = useSlots()

const normalizedShadow = computed(() => {
  const candidate = String(props.shadow || 'always').trim()
  if (['always', 'hover', 'never'].includes(candidate)) {
    return candidate
  }
  return 'always'
})

const cardClasses = computed(() => [
  'ui-card',
  'el-card',
  `is-${normalizedShadow.value}-shadow`,
])

const hasHeader = computed(() => Boolean(props.header) || Boolean(slots.header))
const hasFooter = computed(() => Boolean(props.footer) || Boolean(slots.footer))
</script>

<template>
  <section :class="cardClasses">
    <header v-if="hasHeader" class="ui-card__header el-card__header">
      <slot name="header">
        {{ header }}
      </slot>
    </header>

    <div class="ui-card__body el-card__body" :class="bodyClass" :style="bodyStyle">
      <slot />
    </div>

    <footer v-if="hasFooter" class="ui-card__footer">
      <slot name="footer">
        {{ footer }}
      </slot>
    </footer>
  </section>
</template>

<style scoped>
.ui-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border: 1px solid color-mix(in srgb, var(--qb-border-subtle) 78%, white 22%);
  border-radius: var(--qb-radius-base);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94)),
    var(--qb-bg-card);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.ui-card.is-never-shadow {
  box-shadow: none;
}

.ui-card.is-hover-shadow {
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.ui-card.is-hover-shadow:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.1);
  border-color: color-mix(in srgb, var(--qb-primary-soft-border) 72%, white 28%);
}

.ui-card__header {
  flex: 0 0 auto;
}

.ui-card__body {
  flex: 1 1 auto;
  min-width: 0;
}

.ui-card__footer {
  flex: 0 0 auto;
  padding: 0 24px 24px;
}
</style>
