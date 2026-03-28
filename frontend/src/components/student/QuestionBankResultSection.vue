<script setup>
import QuestionBankEmptyState from './QuestionBankEmptyState.vue'
import QuestionBankSectionHeader from './QuestionBankSectionHeader.vue'

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
  metaText: {
    type: String,
    default: '',
  },
  emptyDescription: {
    type: String,
    default: '',
  },
  hasItems: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <section class="question-bank-result-section">
    <QuestionBankSectionHeader
      :kicker="kicker"
      :title="title"
      :description="description"
    >
      <template v-if="metaText" #meta>
        <span class="question-bank-result-section__meta">{{ metaText }}</span>
      </template>
      <template v-if="$slots.actions" #actions>
        <slot name="actions" />
      </template>
    </QuestionBankSectionHeader>

    <QuestionBankEmptyState
      v-if="!hasItems"
      :description="emptyDescription"
    >
      <template v-if="$slots.emptyActions" #actions>
        <slot name="emptyActions" />
      </template>
    </QuestionBankEmptyState>

    <div v-else class="question-bank-result-section__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.question-bank-result-section {
  display: grid;
  gap: 18px;
}

.question-bank-result-section__meta {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 600;
}

.question-bank-result-section__body {
  min-width: 0;
}
</style>
