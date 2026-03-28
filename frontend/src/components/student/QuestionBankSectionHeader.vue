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
})
</script>

<template>
  <div class="question-bank-section-header">
    <div class="question-bank-section-header__copy">
      <span v-if="kicker" class="question-bank-section-header__kicker">{{ kicker }}</span>
      <h4>{{ title }}</h4>
      <p v-if="description">{{ description }}</p>
    </div>

    <div v-if="$slots.meta || $slots.actions" class="question-bank-section-header__aside">
      <div v-if="$slots.meta" class="question-bank-section-header__meta">
        <slot name="meta" />
      </div>
      <div v-if="$slots.actions" class="question-bank-section-header__actions">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.question-bank-section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.question-bank-section-header__copy h4,
.question-bank-section-header__copy p {
  margin: 0;
}

.question-bank-section-header__kicker {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-info);
  color: var(--qb-text-info-ink);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.question-bank-section-header__copy h4 {
  margin-top: 10px;
  color: var(--qb-text-heading);
  font-size: 20px;
}

.question-bank-section-header__copy p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.question-bank-section-header__aside,
.question-bank-section-header__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

@media (max-width: 720px) {
  .question-bank-section-header {
    flex-direction: column;
  }
}
</style>
