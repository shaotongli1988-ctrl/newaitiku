<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    default: 'info',
  },
  title: {
    type: String,
    default: '',
  },
  subTitle: {
    type: String,
    default: '',
  },
})

const RESULT_VARIANTS = {
  error: {
    accent: 'var(--qb-danger)',
    glow: 'rgba(239, 68, 68, 0.16)',
    glyph: '!',
  },
  success: {
    accent: 'var(--qb-success)',
    glow: 'rgba(34, 197, 94, 0.16)',
    glyph: '✓',
  },
  warning: {
    accent: 'var(--qb-warning)',
    glow: 'rgba(245, 158, 11, 0.16)',
    glyph: '!',
  },
  info: {
    accent: 'var(--qb-primary-student)',
    glow: 'rgba(47, 84, 235, 0.16)',
    glyph: 'i',
  },
  '404': {
    accent: 'var(--qb-text-secondary-strong)',
    glow: 'rgba(71, 85, 105, 0.12)',
    glyph: '404',
  },
}

const normalizedIcon = computed(() => {
  const candidate = String(props.icon || '').trim().toLowerCase()
  return RESULT_VARIANTS[candidate] ? candidate : 'info'
})

const visualStyle = computed(() => ({
  '--ui-result-accent': RESULT_VARIANTS[normalizedIcon.value].accent,
  '--ui-result-glow': RESULT_VARIANTS[normalizedIcon.value].glow,
}))

const iconGlyph = computed(() => RESULT_VARIANTS[normalizedIcon.value].glyph)
const ariaRole = computed(() => (normalizedIcon.value === 'error' ? 'alert' : 'status'))
const ariaLive = computed(() => (normalizedIcon.value === 'error' ? 'assertive' : 'polite'))
</script>

<template>
  <section
    class="ui-result"
    :class="`ui-result--${normalizedIcon}`"
    :style="visualStyle"
    :role="ariaRole"
    :aria-live="ariaLive"
  >
    <div class="ui-result__visual">
      <slot name="icon">
        <div class="ui-result__badge" aria-hidden="true">
          <span class="ui-result__badge-ring"></span>
          <span class="ui-result__badge-core">{{ iconGlyph }}</span>
        </div>
      </slot>
    </div>

    <div class="ui-result__content">
      <h3 v-if="$slots.title || title" class="ui-result__title">
        <slot name="title">
          {{ title }}
        </slot>
      </h3>

      <p v-if="$slots['sub-title'] || subTitle" class="ui-result__subtitle">
        <slot name="sub-title">
          {{ subTitle }}
        </slot>
      </p>

      <div v-if="$slots.default" class="ui-result__body">
        <slot />
      </div>

      <div v-if="$slots.extra" class="ui-result__extra">
        <slot name="extra" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.ui-result {
  --ui-result-accent: var(--qb-primary-student);
  --ui-result-glow: rgba(47, 84, 235, 0.16);
  display: grid;
  justify-items: center;
  gap: 20px;
  width: 100%;
  padding: 28px 20px;
  text-align: center;
}

.ui-result__visual {
  display: grid;
  place-items: center;
}

.ui-result__badge {
  position: relative;
  display: grid;
  place-items: center;
  width: 112px;
  height: 112px;
}

.ui-result__badge-ring,
.ui-result__badge-core {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}

.ui-result__badge-ring {
  border: 1px solid color-mix(in srgb, var(--ui-result-accent) 22%, white 78%);
  background:
    radial-gradient(circle at 50% 50%, var(--ui-result-glow), transparent 72%),
    linear-gradient(155deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.52));
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.65),
    0 18px 30px rgba(15, 23, 42, 0.08);
}

.ui-result__badge-core {
  inset: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(160deg, color-mix(in srgb, var(--ui-result-accent) 18%, white 82%), color-mix(in srgb, var(--ui-result-accent) 58%, white 42%));
  color: color-mix(in srgb, var(--ui-result-accent) 88%, black 12%);
  font-size: 36px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.ui-result__content {
  display: grid;
  justify-items: center;
  gap: 10px;
  max-width: min(560px, 100%);
}

.ui-result__title {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 24px;
  line-height: 1.3;
}

.ui-result__subtitle {
  margin: 0;
  color: var(--qb-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.ui-result__body {
  color: var(--qb-text-secondary-strong);
  font-size: 14px;
  line-height: 1.7;
}

.ui-result__extra {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 6px;
}

.ui-result--error .ui-result__badge-core {
  font-size: 40px;
}

.ui-result--404 .ui-result__badge-core {
  font-size: 24px;
}
</style>
