<script setup>
defineProps({
  description: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <div class="question-bank-empty-state">
    <el-empty :description="description" />
    <div v-if="$slots.default || $slots.actions" class="question-bank-empty-state__extra">
      <slot />
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.question-bank-empty-state {
  padding: 20px;
  border: 1px dashed var(--qb-border-soft);
  border-radius: 22px;
  background: var(--qb-surface-strong);
}

.question-bank-empty-state__extra {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .question-bank-empty-state__extra {
    flex-direction: column;
    align-items: stretch;
  }

  .question-bank-empty-state__extra :deep(.el-button) {
    width: 100%;
  }
}
</style>
