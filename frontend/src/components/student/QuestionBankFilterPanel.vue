<script setup>
defineProps({
  kicker: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  caption: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="question-bank-filter-panel">
    <div class="question-bank-filter-panel__header">
      <div class="question-bank-filter-panel__copy">
        <span v-if="kicker" class="question-bank-filter-panel__kicker">{{ kicker }}</span>
        <h4>{{ title }}</h4>
        <p v-if="description">{{ description }}</p>
      </div>

      <div v-if="caption || $slots.caption" class="question-bank-filter-panel__caption">
        <slot name="caption">
          <span>{{ caption }}</span>
        </slot>
      </div>
    </div>

    <div class="question-bank-filter-panel__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.question-bank-filter-panel {
  display: grid;
  gap: 18px;
  padding: 22px 24px;
  border: 1px solid var(--qb-border-soft);
  border-radius: 22px;
  background: var(--qb-surface-strong);
  box-shadow: var(--qb-shadow-soft);
}

.question-bank-filter-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.question-bank-filter-panel__copy h4,
.question-bank-filter-panel__copy p {
  margin: 0;
}

.question-bank-filter-panel__kicker {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-info);
  color: var(--qb-text-info-ink);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.question-bank-filter-panel__copy h4 {
  margin-top: 10px;
  color: var(--qb-text-heading);
  font-size: 20px;
}

.question-bank-filter-panel__copy p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.question-bank-filter-panel__caption {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.question-bank-filter-panel__body {
  min-width: 0;
}

@media (max-width: 720px) {
  .question-bank-filter-panel__header {
    flex-direction: column;
  }

  .question-bank-filter-panel__caption {
    white-space: normal;
  }
}
</style>
