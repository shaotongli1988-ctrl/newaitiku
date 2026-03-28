<script setup>
defineProps({
  eyebrow: {
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
  <header class="question-bank-page-header">
    <div class="question-bank-page-header__copy">
      <p v-if="eyebrow" class="question-bank-page-header__eyebrow">{{ eyebrow }}</p>
      <h3>{{ title }}</h3>
      <p v-if="description" class="question-bank-page-header__description">{{ description }}</p>
    </div>

    <div v-if="$slots.actions || $slots.meta" class="question-bank-page-header__aside">
      <div v-if="$slots.meta" class="question-bank-page-header__meta">
        <slot name="meta" />
      </div>
      <div v-if="$slots.actions" class="question-bank-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.question-bank-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.question-bank-page-header__copy h3,
.question-bank-page-header__copy p {
  margin: 0;
}

.question-bank-page-header__eyebrow {
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.question-bank-page-header__copy h3 {
  margin-top: 6px;
  color: var(--qb-text-heading);
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.12;
}

.question-bank-page-header__description {
  margin-top: 10px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.75;
}

.question-bank-page-header__aside,
.question-bank-page-header__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.question-bank-page-header__aside {
  align-items: flex-start;
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .question-bank-page-header {
    flex-direction: column;
  }

  .question-bank-page-header__aside {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
