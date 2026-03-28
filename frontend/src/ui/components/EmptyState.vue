<script setup>
import { computed } from 'vue'

const props = defineProps({
  description: {
    type: String,
    default: '',
  },
  imageSize: {
    type: [Number, String],
    default: 88,
  },
})

function normalizeSize(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `${value}px`
  }

  const normalized = String(value || '').trim()
  if (!normalized) {
    return '88px'
  }

  return /^\d+(\.\d+)?$/.test(normalized) ? `${normalized}px` : normalized
}

const illustrationSize = computed(() => normalizeSize(props.imageSize))
</script>

<template>
  <section class="ui-empty" role="status" aria-live="polite">
    <div class="ui-empty__media" :style="{ '--ui-empty-size': illustrationSize }">
      <slot name="image">
        <div class="ui-empty__planet" aria-hidden="true">
          <span class="ui-empty__planet-core"></span>
          <span class="ui-empty__orbit ui-empty__orbit--primary"></span>
          <span class="ui-empty__orbit ui-empty__orbit--secondary"></span>
          <span class="ui-empty__spark ui-empty__spark--left"></span>
          <span class="ui-empty__spark ui-empty__spark--right"></span>
        </div>
      </slot>
    </div>

    <p v-if="$slots.description || description" class="ui-empty__description">
      <slot name="description">
        {{ description }}
      </slot>
    </p>

    <div v-if="$slots.default" class="ui-empty__extra">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.ui-empty {
  display: grid;
  justify-items: center;
  gap: 14px;
  width: 100%;
  padding: 24px 18px;
  text-align: center;
}

.ui-empty__media {
  --ui-empty-size: 88px;
  display: grid;
  place-items: center;
  width: var(--ui-empty-size);
  min-width: var(--ui-empty-size);
  height: var(--ui-empty-size);
}

.ui-empty__planet {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 999px;
  background:
    radial-gradient(
      circle at 35% 32%,
      color-mix(in srgb, var(--qb-text-inverse) 96%, transparent),
      color-mix(in srgb, var(--qb-text-inverse) 20%, transparent) 34%,
      transparent 35%
    ),
    linear-gradient(140deg, rgba(47, 84, 235, 0.18), rgba(76, 110, 245, 0.08));
  box-shadow:
    inset 0 0 0 1px rgba(47, 84, 235, 0.12),
    0 16px 30px rgba(15, 23, 42, 0.08);
}

.ui-empty__planet-core {
  position: absolute;
  inset: 18%;
  border-radius: inherit;
  background:
    radial-gradient(
      circle at 32% 28%,
      var(--qb-surface-strong),
      color-mix(in srgb, var(--qb-text-inverse) 22%, transparent) 30%,
      transparent 31%
    ),
    linear-gradient(160deg, rgba(47, 84, 235, 0.16), rgba(143, 190, 255, 0.56));
}

.ui-empty__orbit {
  position: absolute;
  inset: auto;
  left: 50%;
  top: 50%;
  border-radius: 999px;
  border: 1.5px solid rgba(47, 84, 235, 0.2);
  transform: translate(-50%, -50%) rotate(-18deg);
}

.ui-empty__orbit--primary {
  width: calc(var(--ui-empty-size) * 1.05);
  height: calc(var(--ui-empty-size) * 0.42);
}

.ui-empty__orbit--secondary {
  width: calc(var(--ui-empty-size) * 0.76);
  height: calc(var(--ui-empty-size) * 0.3);
  border-color: rgba(34, 197, 94, 0.18);
  transform: translate(-50%, -50%) rotate(22deg);
}

.ui-empty__spark {
  position: absolute;
  width: calc(var(--ui-empty-size) * 0.1);
  height: calc(var(--ui-empty-size) * 0.1);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(47, 84, 235, 0.86), rgba(14, 116, 144, 0.7));
  box-shadow: 0 0 0 6px rgba(47, 84, 235, 0.08);
}

.ui-empty__spark--left {
  top: 12%;
  left: 8%;
}

.ui-empty__spark--right {
  right: 10%;
  bottom: 14%;
}

.ui-empty__description {
  max-width: min(480px, 100%);
  margin: 0;
  color: var(--qb-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.ui-empty__extra {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}
</style>
